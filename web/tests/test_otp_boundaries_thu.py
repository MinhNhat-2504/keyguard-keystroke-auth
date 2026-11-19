"""Test tự động các ca OTP biên của KeyGuard (task B3).

Ba ca cần kiểm tra, mỗi ca đối chiếu hồ sơ nhịp gõ TRƯỚC và SAU:
  1. Challenge hết hạn sau TTL (5 phút)   -> 410, hồ sơ không đổi.
  2. Dùng lại challenge sau khi OTP đã đúng -> 410, hồ sơ giữ nguyên như sau lượt thành công.
  3. OTP sai                                -> 401, còn 2 lần thử, hồ sơ không đổi.

Cách chạy (ở thư mục gốc của repo):   python tests/test_otp_boundaries_thu.py
Kết quả: in PASS/FAIL từng ca; exit code 0 nếu cả ba đạt, khác 0 nếu có ca lỗi.

Lưu ý khi đọc kết quả:
  * Dữ liệu gõ là DỮ LIỆU TỔNG HỢP sinh bằng bộ sinh số ngẫu nhiên cố định (seed), không phải người thật.
  * Toàn bộ dữ liệu nằm trong thư mục tạm, bị xóa sau khi chạy; không đụng tới data/ thật.
  * "Hết hạn" được MÔ PHỎNG bằng cách đẩy đồng hồ time.time() tiến thêm OTP_TTL_SECONDS + 1 giây;
    test KHÔNG chờ thật 5 phút.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Phải đặt biến môi trường TRƯỚC khi import app, vì app tính thư mục dữ liệu ngay lúc import.
_TMP = tempfile.TemporaryDirectory(prefix="keyguard_otp_test_")
os.environ["KEYGUARD_DATA_DIR"] = _TMP.name
os.environ["KEYGUARD_SHOW_OTP"] = "1"          # chỉ trong test: lấy OTP từ phản hồi thay vì đọc console
os.environ["KEYGUARD_VERIFY_LIMIT"] = "1000"   # tránh bị giới hạn 10 lần/phút của /api/verify
os.environ["KEYGUARD_MAX_PENDING"] = "50"      # cho phép nhiều challenge đang chờ cùng lúc

import app as ka  # noqa: E402

KEYS = [".", "t", "i", "e", "5", "R", "o", "a", "n", "l", "Enter"]
BASE_HOLD = [0.09, 0.08, 0.10, 0.09, 0.11, 0.10, 0.09, 0.08, 0.10, 0.09, 0.12]  # giây
BASE_GAP = [0.22, 0.18, 0.20, 0.25, 0.30, 0.19, 0.21, 0.17, 0.20, 0.23]          # giây (down -> down)


def make_sample(rng: np.random.Generator, slow: float = 1.0, wobble: float = 0.05) -> list[dict]:
    """Sinh một lần gõ tổng hợp. `slow` > 1 làm nhịp chậm đi (dùng để tạo lần gõ lạ)."""
    events, t = [], 0.0
    for i, key in enumerate(KEYS):
        hold = BASE_HOLD[i] * slow * (1 + rng.normal(0, wobble))
        events.append({"key": key, "type": "down", "t": round(t * 1000, 3)})
        events.append({"key": key, "type": "up", "t": round((t + hold) * 1000, 3)})
        if i < len(BASE_GAP):
            t += max(BASE_GAP[i] * slow * (1 + rng.normal(0, wobble)), hold + 0.02)
    return sorted(events, key=lambda e: e["t"])


def snapshot(profile_id: str) -> dict:
    """Trạng thái hồ sơ: số mẫu và hash nội dung (băm JSON đã sắp xếp khóa)."""
    path = ka.PROFILES_DIR / f"{profile_id}.json"
    profile = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(profile, sort_keys=True, separators=(",", ":")).encode()
    return {"n_samples": len(profile["samples"]), "sha256": hashlib.sha256(canonical).hexdigest()}


class OtpBoundaryTests(unittest.TestCase):
    """Mỗi ca dùng MỘT TÀI KHOẢN RIÊNG vừa đăng ký, để hồ sơ của ca này không ảnh hưởng ca khác."""

    _counter = 0

    def setUp(self):
        OtpBoundaryTests._counter += 1
        self.client = ka.app.test_client()
        self.rng = np.random.default_rng(2026 + OtpBoundaryTests._counter)
        self.username = f"test_otp_user_{OtpBoundaryTests._counter}"
        samples = [make_sample(self.rng) for _ in range(20)]
        r = self.client.post("/api/enroll", json={"username": self.username, "samples": samples})
        self.assertEqual(r.status_code, 200, f"Đăng ký thất bại: {r.get_json()}")
        accounts = json.loads(ka.ACCOUNTS_FILE.read_text(encoding="utf-8"))
        self.profile_id = accounts[self.username.casefold()]["id"]

    def new_challenge(self) -> tuple[str, str]:
        """Gõ một lần nhịp rất chậm để bị từ chối, trả về (challenge_id, otp)."""
        odd = make_sample(self.rng, slow=3.0)
        r = self.client.post("/api/verify", json={"username": self.username, "events": odd})
        body = r.get_json()
        self.assertEqual(r.status_code, 200, body)
        self.assertTrue(body["otp_required"], f"Lần gõ lạ không bị yêu cầu OTP: {body}")
        return body["challenge_id"], body["demo_otp"]

    def post_otp(self, cid: str, otp: str):
        return self.client.post("/api/verify-otp", json={"challenge_id": cid, "otp": otp})

    # ---- Ca 1 ----
    def test_1_expired_challenge_returns_410_and_profile_unchanged(self):
        cid, otp = self.new_challenge()
        before = snapshot(self.profile_id)
        real_time = time.time
        with mock.patch.object(ka.time, "time", lambda: real_time() + ka.OTP_TTL_SECONDS + 1):
            r = self.post_otp(cid, otp)  # OTP ĐÚNG nhưng đã quá hạn
        self.assertEqual(r.status_code, 410, r.get_json())
        self.assertFalse(r.get_json()["success"])
        self.assertEqual(snapshot(self.profile_id), before, "Hồ sơ bị đổi dù challenge đã hết hạn")

    # ---- Ca 2 ----
    def test_2_replay_after_success_returns_410_and_profile_unchanged_since_success(self):
        cid, otp = self.new_challenge()
        before = snapshot(self.profile_id)
        r1 = self.post_otp(cid, otp)
        self.assertEqual(r1.status_code, 200, r1.get_json())
        after_success = snapshot(self.profile_id)
        self.assertEqual(after_success["n_samples"], before["n_samples"] + 1, "Lượt thành công phải thêm đúng 1 mẫu")
        self.assertNotEqual(after_success["sha256"], before["sha256"], "Lượt thành công phải cập nhật hồ sơ")
        r2 = self.post_otp(cid, otp)  # dùng lại đúng challenge và OTP đó
        self.assertEqual(r2.status_code, 410, r2.get_json())
        self.assertEqual(snapshot(self.profile_id), after_success, "Replay làm hồ sơ đổi so với sau lượt thành công")

    # ---- Ca 3 ----
    def test_3_wrong_otp_returns_401_and_profile_unchanged(self):
        cid, otp = self.new_challenge()
        before = snapshot(self.profile_id)
        wrong = "000000" if otp != "000000" else "111111"
        r = self.post_otp(cid, wrong)
        self.assertEqual(r.status_code, 401, r.get_json())
        self.assertEqual(r.get_json()["attempts_left"], ka.OTP_MAX_ATTEMPTS - 1)
        self.assertEqual(snapshot(self.profile_id), before, "OTP sai nhưng hồ sơ bị đổi")


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\nTỔNG KẾT: {passed}/{result.testsRun} ca đạt")
    _TMP.cleanup()
    sys.exit(0 if result.wasSuccessful() else 1)