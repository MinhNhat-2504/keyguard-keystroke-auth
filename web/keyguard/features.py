"""Trích đặc trưng nhịp gõ phím theo đúng định dạng của CMU Keystroke Benchmark.

Câu gõ cố định là ".tie5Roanl" rồi nhấn Enter (11 phím). Mỗi lần gõ cho ra
31 đặc trưng, đơn vị giây:

- H.<k>      thời gian giữ phím k (hold) = up(k) - down(k)
- DD.<k1>.<k2> thời gian giữa hai lần nhấn liên tiếp = down(k2) - down(k1)
- UD.<k1>.<k2> thời gian từ lúc nhả k1 đến lúc nhấn k2 = down(k2) - up(k1)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PHRASE = ".tie5Roanl"

# Tên phím theo cách đặt tên cột của CMU, và ký tự tương ứng (đã viết thường).
CMU_KEYS = ["period", "t", "i", "e", "five", "Shift.r", "o", "a", "n", "l", "Return"]
EXPECTED_CHARS = [".", "t", "i", "e", "5", "r", "o", "a", "n", "l", "enter"]

FEATURE_NAMES: list[str] = []
for _i, _k in enumerate(CMU_KEYS):
    FEATURE_NAMES.append(f"H.{_k}")
    if _i + 1 < len(CMU_KEYS):
        _n = CMU_KEYS[_i + 1]
        FEATURE_NAMES += [f"DD.{_k}.{_n}", f"UD.{_k}.{_n}"]

N_FEATURES = len(FEATURE_NAMES)  # 31

# Phím bổ trợ không tính là một lần gõ (ví dụ Shift khi gõ chữ R hoa).
MODIFIER_KEYS = {"shift", "control", "alt", "meta", "capslock", "altgraph"}


class InvalidSampleError(ValueError):
    """Lần gõ không khớp câu cố định (gõ sai, thiếu phím, thiếu sự kiện)."""


def _normalize_key(key: str) -> str:
    key = str(key)
    if key.lower() in ("enter", "return"):
        return "enter"
    return key.lower()


def events_to_keystrokes(events: list[dict]) -> list[tuple[str, float, float]]:
    """Ghép mỗi sự kiện 'down' với sự kiện 'up' kế tiếp của cùng phím.

    Trả về danh sách (phím, thời điểm nhấn, thời điểm nhả) theo thứ tự nhấn, đơn vị ms.
    """
    ordered = sorted(events, key=lambda e: float(e["t"]))
    open_downs: dict[str, float] = {}
    strokes: list[tuple[str, float, float]] = []
    for ev in ordered:
        key = _normalize_key(ev["key"])
        if key in MODIFIER_KEYS:
            continue
        etype = str(ev["type"]).lower()
        t = float(ev["t"])
        if etype in ("down", "keydown"):
            if key in open_downs:  # giữ phím lâu sinh auto-repeat: bỏ qua lần nhấn lặp
                continue
            open_downs[key] = t
        elif etype in ("up", "keyup"):
            if key not in open_downs:
                continue
            strokes.append((key, open_downs.pop(key), t))
        else:
            raise InvalidSampleError(f"Loại sự kiện không hợp lệ: {ev['type']!r}")
    if open_downs:
        raise InvalidSampleError(f"Có phím được nhấn nhưng không thấy nhả: {sorted(open_downs)}")
    strokes.sort(key=lambda s: s[1])
    return strokes


def extract_features(events: list[dict]) -> np.ndarray:
    """Chuyển một lần gõ (danh sách sự kiện phím, t tính bằng ms) thành vector 31 đặc trưng."""
    strokes = events_to_keystrokes(events)
    typed = [s[0] for s in strokes]
    if typed != EXPECTED_CHARS:
        raise InvalidSampleError(
            f"Chuỗi gõ {''.join(c if c != 'enter' else '⏎' for c in typed)!r} "
            f"không khớp {PHRASE!r} + Enter"
        )
    down = np.array([s[1] for s in strokes]) / 1000.0
    up = np.array([s[2] for s in strokes]) / 1000.0
    feats: list[float] = []
    for i in range(len(strokes)):
        feats.append(up[i] - down[i])
        if i + 1 < len(strokes):
            feats.append(down[i + 1] - down[i])
            feats.append(down[i + 1] - up[i])
    return np.asarray(feats, dtype=float)


def features_to_events(x: np.ndarray) -> list[dict]:
    """Phép ngược của extract_features: dựng lại sự kiện phím từ một dòng CMU.

    Dùng để kiểm thử và để tạo dữ liệu mẫu cho web demo, không dùng để huấn luyện.
    """
    x = np.asarray(x, dtype=float)
    chars = [c if c != "enter" else "Enter" for c in EXPECTED_CHARS]
    chars[5] = "R"
    events: list[dict] = []
    t_down = 0.0
    for i, ch in enumerate(chars):
        hold = x[FEATURE_NAMES.index(f"H.{CMU_KEYS[i]}")]
        events.append({"key": ch, "type": "down", "t": round(t_down * 1000, 3)})
        events.append({"key": ch, "type": "up", "t": round((t_down + hold) * 1000, 3)})
        if i + 1 < len(chars):
            t_down += x[FEATURE_NAMES.index(f"DD.{CMU_KEYS[i]}.{CMU_KEYS[i + 1]}")]
    return sorted(events, key=lambda e: e["t"])


def load_cmu(path: str | Path) -> pd.DataFrame:
    """Đọc DSL-StrongPasswordData.csv. Cột: subject, sessionIndex, rep + 31 đặc trưng."""
    df = pd.read_csv(path)
    missing = [c for c in ["subject", "sessionIndex", "rep", *FEATURE_NAMES] if c not in df.columns]
    if missing:
        raise ValueError(f"File CMU thiếu cột: {missing}")
    return df[["subject", "sessionIndex", "rep", *FEATURE_NAMES]]
