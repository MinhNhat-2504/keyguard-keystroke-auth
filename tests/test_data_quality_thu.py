"""Test cho script kiểm chất lượng dữ liệu (task B1), dùng DỮ LIỆU GIẢ trong tests/fake_quality_data/.

Chạy (ở thư mục gốc repo):   python tests/test_data_quality_thu.py
Kiểm tra:
  1. Mọi nhóm lỗi trong dữ liệu giả đều được phát hiện đúng số lượng (so với EXPECTED.json).
  2. File dữ liệu gốc không bị sửa (SHA-256 trước = sau).
  3. Thông tin "chưa ghi nhận" (thiếu thiết bị, thiếu thời gian) được xếp riêng khỏi "lỗi".
  4. Bộ dữ liệu sạch (chỉ FAKE01) cho exit code 0; bộ có lỗi cho exit code 1.
  5. Script từ chối ghi báo cáo vào bên trong thư mục dữ liệu.
Dữ liệu giả không phải của người thật. Mọi báo cáo của test ghi vào thư mục tạm.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAKE = ROOT / "tests" / "fake_quality_data"

spec = importlib.util.spec_from_file_location("check_data_quality", ROOT / "scripts" / "check_data_quality.py")
cdq = importlib.util.module_from_spec(spec)
sys.modules["check_data_quality"] = cdq
spec.loader.exec_module(cdq)


class DataQualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dq_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_1_all_error_groups_detected_with_expected_counts(self):
        expected = json.loads((FAKE / "EXPECTED.json").read_text(encoding="utf-8"))
        report = cdq.run_check(FAKE, self.tmp / "out")
        self.assertEqual(report["issue_counts"], dict(sorted(expected.items())))

    def test_2_raw_files_unchanged(self):
        before = {p.name: cdq.sha256_file(p) for p in FAKE.glob("*.jsonl")}
        report = cdq.run_check(FAKE, self.tmp / "out")
        after = {p.name: cdq.sha256_file(p) for p in FAKE.glob("*.jsonl")}
        self.assertEqual(before, after)
        self.assertTrue(report["raw_unchanged"])

    def test_3_not_recorded_is_separate_from_errors(self):
        # FAKE01 không có lỗi nào, chỉ thiếu thiết bị => 0 lỗi, nhưng có 1 mục "chưa ghi nhận"
        only = self.tmp / "only"
        only.mkdir()
        shutil.copy(FAKE / "FAKE01.jsonl", only / "FAKE01.jsonl")
        report = cdq.run_check(only, self.tmp / "out")
        self.assertEqual(report["errors"], 0)
        self.assertEqual(report["issue_counts"], {"CHUA_GHI_NHAN/THIEU_THIET_BI": 1})

    def test_4_exit_codes(self):
        only = self.tmp / "only"
        only.mkdir()
        shutil.copy(FAKE / "FAKE01.jsonl", only / "FAKE01.jsonl")
        self.assertEqual(cdq.main(["--data-dir", str(only), "--out-dir", str(self.tmp / "o1")]), 0)
        self.assertEqual(cdq.main(["--data-dir", str(FAKE), "--out-dir", str(self.tmp / "o2")]), 1)

    def test_5_refuses_report_inside_data_dir(self):
        with self.assertRaises(SystemExit):
            cdq.run_check(FAKE, FAKE / "report_inside")
        self.assertFalse((FAKE / "report_inside").exists())


if __name__ == "__main__":
    result = unittest.main(exit=False, verbosity=2).result
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"\nTỔNG KẾT: {passed}/{result.testsRun} ca đạt")
    sys.exit(0 if result.wasSuccessful() else 1)
