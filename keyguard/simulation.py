"""Mô phỏng một chuỗi đăng nhập theo thời gian, dùng đúng các hàm của keyguard/model.py.

Ba chính sách cập nhật hồ sơ (giữ tối đa cfg["window"] lần gõ gần nhất):
    static   : hồ sơ giữ nguyên sau khi đăng ký;
    accept   : chỉ thêm lần gõ được nhịp gõ chấp nhận;
    fallback : xác thực theo rủi ro. Nhịp gõ không khớp thì hỏi thêm một bước xác minh
               (ví dụ OTP); chủ tài khoản qua được bước đó nên lần gõ nào của chủ cũng
               được thêm vào hồ sơ. Khi đó FRR = tỉ lệ lần đăng nhập phải xác minh thêm.
"""

from __future__ import annotations

import numpy as np

from keyguard.model import build_profile, profile_z

POLICIES = ["static", "accept", "fallback"]
POLICY_LABELS = {
    "static": "Không cập nhật",
    "accept": "Cập nhật khi được chấp nhận",
    "fallback": "Cập nhật cả sau xác minh thêm (OTP)",
}


def simulate_user(
    X: np.ndarray,
    imp_X: np.ndarray,
    cfg: dict,
    tau: float,
    policy: str,
    checkpoint_every: int = 50,
) -> tuple[np.ndarray, np.ndarray]:
    """Đăng ký bằng cfg["n_enroll"] lần gõ đầu của X, rồi đăng nhập lần lượt bằng phần còn lại.

    Kẻ gian (imp_X) thử đăng nhập ngay sau khi đăng ký và sau mỗi `checkpoint_every`
    lần gõ; lần thử của kẻ gian không cập nhật hồ sơ.
    Trả về (z của từng lần đăng nhập thật, z của kẻ gian gộp qua các mốc).
    """
    if policy not in POLICIES:
        raise ValueError(f"Chính sách không hợp lệ: {policy}")
    n = cfg["n_enroll"]
    profile = build_profile(X[:n], cfg)
    zg, zi = np.empty(len(X) - n), []
    for t in range(n, len(X)):
        if t == n or t % checkpoint_every == 0:
            zi.append(profile_z(profile, imp_X))
        z = float(profile_z(profile, X[t])[0])
        zg[t - n] = z
        if policy == "fallback" or (policy == "accept" and z <= tau):
            profile = build_profile(np.vstack([profile["samples"], X[t]]), cfg)
    return zg, np.concatenate(zi)
