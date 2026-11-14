#!/usr/bin/env python3
"""Kiểm tra chất lượng dữ liệu nhịp gõ tự thu (task B1). KHÔNG sửa dữ liệu gốc.

Đọc mọi file *.jsonl trong thư mục dữ liệu (mặc định data/collected), phát hiện và PHÂN LOẠI vấn đề:

  Nhóm LOI (dữ liệu có lỗi):
    JSON_KHONG_DOC_DUOC     dòng không phải JSON hợp lệ
    THIEU_TRUONG            thiếu participant_id / session / rep / events
    SAI_MA_NGUOI            participant_id trong dòng khác tên file
    KHOA_TRUNG              trùng khóa (người, phiên, lần gõ)            -> severity error
    SU_KIEN_KHONG_HOP_LE    sự kiện phím sai cấu trúc, sai câu mẫu, thiếu phím nhả, t không hợp lệ
    REP_KHONG_LIEN_TUC      số lần gõ trong một phiên bị nhảy cách (thiếu số)   -> severity warning

  Nhóm CHUA_GHI_NHAN (thông tin KHÔNG được thu, không phải lỗi của dòng đó):
    THIEU_THOI_GIAN         dòng không có collected_at
    THIEU_THIET_BI          dòng không có trường nào mô tả thiết bị (device / user_agent / platform);
                            báo một dòng cho mỗi file kèm số dòng bị thiếu

Script không điền, không đoán và không "sửa" bất kỳ giá trị nào. Nó chỉ đọc file gốc, rồi ghi báo cáo vào
thư mục khác. SHA-256 của từng file gốc được tính trước và sau khi chạy để chứng minh không bị đổi.

Cách chạy (ở thư mục gốc repo):
    python scripts/check_data_quality.py
    python scripts/check_data_quality.py --data-dir data/collected --out-dir docs/data_quality

Exit code: 0 nếu không có lỗi mức error; 1 nếu có lỗi mức error; 2 nếu file gốc bị đổi hoặc không chạy được.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from keyguard.features import (  # noqa: E402
    MODIFIER_KEYS,
    PHRASE,
    InvalidSampleError,
    extract_features,
)

REQUIRED_FIELDS = ("participant_id", "session", "rep", "events")
DEVICE_FIELDS = ("device", "device_class", "user_agent", "platform")
EXPECTED_DOWN_KEYS = list(PHRASE) + ["enter"]
CSV_FIELDS = ["participant", "file", "line", "session", "rep", "code", "category", "severity", "detail"]

LOI, CHUA = "LOI", "CHUA_GHI_NHAN"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def case_error(events: list[dict]) -> str | None:
    """Chuỗi gõ phải đúng hoa/thường (R hoa) + Enter, chỉ xét sự kiện 'down'."""
    typed, open_keys = [], set()
    for ev in sorted(events, key=lambda e: float(e["t"])):
        key = str(ev["key"])
        low = key.lower()
        if low in MODIFIER_KEYS:
            continue
        if str(ev["type"]).lower() in ("down", "keydown"):
            if low in open_keys:
                continue
            open_keys.add(low)
            typed.append("enter" if low in ("enter", "return") else key)
        else:
            open_keys.discard("enter" if low == "return" else low)
    if typed != EXPECTED_DOWN_KEYS:
        return "chuỗi gõ không khớp câu mẫu (kể cả hoa/thường)"
    return None


def events_error(events) -> str | None:
    """Trả về mô tả lỗi của danh sách sự kiện, hoặc None nếu hợp lệ."""
    if not isinstance(events, list) or not events:
        return "events không phải danh sách không rỗng"
    for ev in events:
        if not isinstance(ev, dict) or not all(k in ev for k in ("key", "type", "t")):
            return "có sự kiện thiếu key/type/t"
        if isinstance(ev["t"], bool) or not isinstance(ev["t"], (int, float)) or not math.isfinite(ev["t"]):
            return "có thời điểm t không phải số hữu hạn"
        if not isinstance(ev["key"], str) or not isinstance(ev["type"], str):
            return "key/type không phải chuỗi"
        if ev["type"].lower() not in ("down", "up", "keydown", "keyup"):
            return f"loại sự kiện lạ: {ev['type']!r}"
    msg = case_error(events)
    if msg:
        return msg
    try:
        feats = extract_features(events)
    except InvalidSampleError as e:
        return f"không trích được đặc trưng: {e}"
    if len(feats) != 31 or not all(math.isfinite(x) for x in feats):
        return "đặc trưng không hợp lệ (không đủ 31 giá trị hữu hạn)"
    return None


def check_file(path: Path) -> tuple[list[dict], dict]:
    """Kiểm một file. Trả về (danh sách vấn đề, thống kê của người tham gia)."""
    issues: list[dict] = []
    stem = path.stem
    records: list[tuple[int, dict]] = []

    def add(line, rec, code, category, severity, detail):
        issues.append({
            "participant": stem, "file": path.name, "line": line,
            "session": rec.get("session", "") if rec else "", "rep": rec.get("rep", "") if rec else "",
            "code": code, "category": category, "severity": severity, "detail": detail,
        })

    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            if not raw.strip():
                continue
            try:
                rec = json.loads(raw)
                if not isinstance(rec, dict):
                    raise ValueError("không phải đối tượng JSON")
            except ValueError as e:
                add(n, None, "JSON_KHONG_DOC_DUOC", LOI, "error", str(e))
                continue
            records.append((n, rec))

    seen: dict[tuple, list[int]] = defaultdict(list)
    per_session_reps: dict[str, list[int]] = defaultdict(list)
    days: set[str] = set()
    n_no_time = n_no_device = 0

    for n, rec in records:
        missing = [k for k in REQUIRED_FIELDS if k not in rec]
        if missing:
            add(n, rec, "THIEU_TRUONG", LOI, "error", "thiếu: " + ", ".join(missing))
        elif rec["participant_id"] != stem:
            add(n, rec, "SAI_MA_NGUOI", LOI, "error", f"participant_id {rec['participant_id']!r} khác tên file")
        if not missing:
            seen[(rec["participant_id"], rec["session"], rec["rep"])].append(n)
            if isinstance(rec["rep"], int) and not isinstance(rec["rep"], bool):
                per_session_reps[str(rec["session"])].append(rec["rep"])
            err = events_error(rec["events"])
            if err:
                add(n, rec, "SU_KIEN_KHONG_HOP_LE", LOI, "error", err)
        ts = rec.get("collected_at")
        if ts:
            days.add(str(ts)[:10])
        else:
            n_no_time += 1
            add(n, rec, "THIEU_THOI_GIAN", CHUA, "info", "dòng không có collected_at")
        if not any(rec.get(k) for k in DEVICE_FIELDS):
            n_no_device += 1

    for key, lines in seen.items():
        if len(lines) > 1:
            for n in lines:
                rec = dict(records[[r[0] for r in records].index(n)][1])
                add(n, rec, "KHOA_TRUNG", LOI, "error",
                    f"khóa (người,phiên,rep)={key} xuất hiện ở các dòng {lines}")

    for sess, reps in per_session_reps.items():
        present = set(reps)
        gaps = [r for r in range(1, max(present) + 1) if r not in present]
        if gaps:
            add("", {"session": sess}, "REP_KHONG_LIEN_TUC", LOI, "warning",
                f"phiên {sess} thiếu số lần gõ: {gaps}")

    if n_no_device:  # một dòng cho cả file, để báo cáo không bị ngập bởi hàng trăm dòng giống nhau
        add("", None, "THIEU_THIET_BI", CHUA, "info",
            f"{n_no_device}/{len(records)} dòng không có trường mô tả thiết bị ({'/'.join(DEVICE_FIELDS)})")

    stats = {
        "records": len(records),
        "sessions": sorted(per_session_reps),
        "days": sorted(days),
        "records_without_time": n_no_time,
        "records_without_device": n_no_device,
    }
    return issues, stats


def run_check(data_dir: Path, out_dir: Path) -> dict:
    data_dir, out_dir = data_dir.resolve(), out_dir.resolve()
    if out_dir == data_dir or data_dir in out_dir.parents:
        raise SystemExit("Thư mục báo cáo không được nằm trong thư mục dữ liệu (tránh ghi đè dữ liệu gốc).")
    files = sorted(data_dir.glob("*.jsonl"))
    if not files:
        raise SystemExit(f"Không thấy file *.jsonl nào trong {data_dir}")

    hashes_before = {p.name: sha256_file(p) for p in files}
    all_issues: list[dict] = []
    people: dict[str, dict] = {}
    for p in files:
        issues, stats = check_file(p)
        all_issues += issues
        people[p.stem] = stats

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "data_quality_issues.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(all_issues)

    hashes_after = {p.name: sha256_file(p) for p in files}
    unchanged = hashes_before == hashes_after
    counts = Counter((i["category"], i["code"]) for i in all_issues)
    report = {
        "data_dir": str(data_dir.name),
        "n_files": len(files),
        "n_records": sum(s["records"] for s in people.values()),
        "raw_unchanged": unchanged,
        "issue_counts": {f"{c}/{k}": v for (c, k), v in sorted(counts.items())},
        "errors": sum(1 for i in all_issues if i["severity"] == "error"),
        "warnings": sum(1 for i in all_issues if i["severity"] == "warning"),
        "per_participant": people,
        "sha256_before": hashes_before,
        "sha256_after": hashes_after,
        "note": "Nhóm CHUA_GHI_NHAN là thông tin không được thu, không phải lỗi; script không điền hay đoán giá trị.",
    }
    with open(out_dir / "data_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Kiểm tra chất lượng dữ liệu nhịp gõ tự thu (không sửa dữ liệu gốc).")
    ap.add_argument("--data-dir", default=str(ROOT / "data" / "collected"))
    ap.add_argument("--out-dir", default=str(ROOT / "docs" / "data_quality"))
    args = ap.parse_args(argv)
    report = run_check(Path(args.data_dir), Path(args.out_dir))

    print(f"Đã kiểm {report['n_files']} file, {report['n_records']} dòng hợp lệ về mặt JSON.")
    print("Dữ liệu gốc không đổi (SHA-256 trước = sau):", "ĐÚNG" if report["raw_unchanged"] else "SAI")
    print("Số vấn đề theo loại:")
    for k, v in report["issue_counts"].items():
        print(f"  {k}: {v}")
    print(f"Lỗi mức error: {report['errors']}, cảnh báo: {report['warnings']}")
    print(f"Báo cáo: {Path(args.out_dir) / 'data_quality_report.json'} và data_quality_issues.csv")
    if not report["raw_unchanged"]:
        return 2
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
