#!/usr/bin/env python3
"""Tạo docs/live_test.csv từ attempts.csv và in các số cho bảng kết quả 2.6.

Cách dùng (đơn giản nhất, đặt file này cạnh attempts.csv):
    python make_live_test.py

Cách dùng đầy đủ:
    python make_live_test.py attempts.csv
    python make_live_test.py attempts.csv -o docs/live_test.csv --impostor-people 8

- Gộp dòng event=otp vào đúng lượt verify (theo attempt_id).
- Chỉ giữ role = genuine / impostor (bỏ unspecified).
- FAR/FRR tính theo lượt, ghi tử số/mẫu số.
- Nếu tester_id trống (đợt thử không ghi mã), dùng --impostor-people N để ghi số người
  theo trí nhớ. Chỉ điền số đúng sự thật.
"""
import argparse
import csv
import sys
from pathlib import Path

OUT_FIELDS = ["time", "attempt_id", "account_ref", "role", "tester_id", "device",
              "accepted", "confidence", "otp_required", "otp_result", "otp_tries"]


def frac(num, den):
    return f"{num}/{den} = {num / den * 100:.1f}%" if den else f"{num}/{den} = n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("attempts", nargs="?", default="attempts.csv")
    ap.add_argument("-o", "--out", default="docs/live_test.csv")
    ap.add_argument("--impostor-people", type=int, default=None,
                    help="số người đóng kẻ gian (khi tester_id trống)")
    args = ap.parse_args()

    with open(args.attempts, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    verifies, otps = {}, {}
    for r in rows:
        if r["event"] == "verify":
            verifies[r["attempt_id"]] = r
        elif r["event"] == "otp":
            otps.setdefault(r["attempt_id"], []).append(r)

    dropped = sum(1 for r in verifies.values() if r["role"] not in ("genuine", "impostor"))
    out = []
    for aid, v in verifies.items():
        if v["role"] not in ("genuine", "impostor"):
            continue
        tries = otps.get(aid, [])
        results = [t["otp_result"] for t in tries]
        final = "ok" if "ok" in results else (results[-1] if results else "")
        out.append({**{k: v.get(k, "") for k in OUT_FIELDS if k not in ("otp_result", "otp_tries")},
                    "otp_result": final, "otp_tries": len(tries)})
    out.sort(key=lambda r: r["time"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_FIELDS)
        w.writeheader()
        w.writerows(out)

    gen = [r for r in out if r["role"] == "genuine"]
    imp = [r for r in out if r["role"] == "impostor"]
    acc = lambda rs: sum(1 for r in rs if r["accepted"] == "1")
    gen_rej = [r for r in gen if r["accepted"] != "1"]
    imp_rej = [r for r in imp if r["accepted"] != "1"]
    gen_otp_ok = sum(1 for r in gen_rej if r["otp_result"] == "ok")
    imp_otp_ok = sum(1 for r in imp_rej if r["otp_result"] == "ok")

    ids = {r["tester_id"] for r in imp if r["tester_id"]}
    if not ids and args.impostor_people is None and sys.stdin.isatty():
        ans = input("tester_id trống. Có bao nhiêu bạn đóng kẻ gian (số bạn nhớ thật sự, Enter để bỏ qua)? ").strip()
        if ans.isdigit():
            args.impostor_people = int(ans)
    if ids:
        people = f"{len(ids)} (đếm từ tester_id)"
    elif args.impostor_people:
        people = f"{args.impostor_people} (theo trí nhớ, tester_id không được ghi)"
    else:
        people = "chưa rõ (tester_id trống, dùng --impostor-people N)"

    print(f"Đã ghi {len(out)} dòng vào {args.out} (bỏ {dropped} lượt unspecified)\n")
    print("=== BẢNG KẾT QUẢ 2.6 ===")
    print(f"Số người đóng kẻ gian : {people}")
    print(f"Số lượt impostor      : {len(imp)}  (yêu cầu >= 10 người)")
    print(f"Số lượt genuine       : {len(gen)}  (yêu cầu >= 20 lượt)")
    print(f"FAR (impostor nhận ngay): {frac(acc(imp), len(imp))}")
    print(f"FRR (genuine bị đòi OTP): {frac(len(gen_rej), len(gen))}")
    print(f"Sau OTP - genuine bị từ chối nhưng qua OTP : {frac(gen_otp_ok, len(gen_rej))}")
    print(f"Sau OTP - impostor qua được OTP            : {frac(imp_otp_ok, len(imp_rej))}")
    if len(gen) < 20:
        print(f"\n! Mới có {len(gen)} lượt genuine, cần thêm {20 - len(gen)}.")
    if not ids and not args.impostor_people:
        print("! Chưa có số người đóng kẻ gian cho bảng kết quả.")


if __name__ == "__main__":
    sys.exit(main())