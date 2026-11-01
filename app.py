"""KeyGuard web: thu dữ liệu nhịp gõ + demo đăng ký / đăng nhập bằng nhịp gõ.

Trang:   /          thu dữ liệu (collector)
         /register  đăng ký tài khoản (gõ n lần, n lấy từ models/model_config.json)
         /login     đăng nhập; nếu nhịp gõ không khớp thì chuyển sang xác minh OTP mô phỏng
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import math
import os
import re
import secrets
import sys
import time
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from keyguard.features import (  # noqa: E402
    MODIFIER_KEYS,
    PHRASE,
    InvalidSampleError,
    extract_features,
)
from keyguard.model import enroll, load_config, update, verify  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("keyguard.web")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB là quá đủ cho 20 lần gõ

DATA_DIR = ROOT / "data"
COLLECTED_DIR = DATA_DIR / "collected"
PROFILES_DIR = DATA_DIR / "profiles"
for _d in (COLLECTED_DIR, PROFILES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

PARTICIPANTS_FILE = DATA_DIR / "participants.json"   # các mã ẩn danh đã cấp
ACCOUNTS_FILE = DATA_DIR / "accounts.json"           # tên đăng nhập -> mã hồ sơ nội bộ
CHALLENGES_FILE = DATA_DIR / "challenges.json"       # OTP đang chờ xác nhận
LOCK_FILE = DATA_DIR / ".lock"

MAX_SESSIONS = 3
MAX_REPS = 40
MAX_EVENTS_PER_SAMPLE = 200
MAX_ENROLL_SAMPLES = 100
USERNAME_MAX_LEN = 50
OTP_TTL_SECONDS = 5 * 60
OTP_MAX_ATTEMPTS = 3
# Demo: OTP được "gửi" bằng cách in ra console server và trả kèm response để trang hiển thị
# như một tin nhắn SMS giả lập. Đặt KEYGUARD_SHOW_OTP=0 để tắt việc trả OTP về trình duyệt.
SHOW_OTP_IN_RESPONSE = os.environ.get("KEYGUARD_SHOW_OTP", "1") != "0"

PARTICIPANT_RE = re.compile(r"^P\d{2,4}$")
PROFILE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
EXPECTED_DOWN_KEYS = list(PHRASE) + ["enter"]


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400, **extra):
        super().__init__(message)
        self.message, self.status, self.extra = message, status, extra


# ----------------------------------------------------------------------------------------
# Lưu trữ: khóa file (chạy được trên Windows/Linux, nhiều worker) + ghi nguyên tử
# ----------------------------------------------------------------------------------------
@contextmanager
def data_lock(timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            try:  # khóa bị bỏ lại do tiến trình chết: xóa nếu quá cũ
                if time.time() - LOCK_FILE.stat().st_mtime > 30:
                    LOCK_FILE.unlink(missing_ok=True)
                    continue
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise ApiError("Hệ thống đang bận, vui lòng thử lại.", 503)
            time.sleep(0.02)
    try:
        yield
    finally:
        LOCK_FILE.unlink(missing_ok=True)


def read_json(path: Path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def write_json_atomic(path: Path, obj) -> None:
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def safe_path(base: Path, filename: str) -> Path:
    """Đường dẫn file nằm CHẮC CHẮN trong `base` (chặn ../ và đường dẫn tuyệt đối)."""
    base = base.resolve()
    p = (base / filename).resolve()
    if p.parent != base:
        raise ApiError("Định danh không hợp lệ.", 400)
    return p


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


# ----------------------------------------------------------------------------------------
# Kiểm tra dữ liệu đầu vào
# ----------------------------------------------------------------------------------------
def json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Dữ liệu gửi lên phải là một đối tượng JSON.", 400)
    return data


def check_case(events: list[dict]) -> None:
    """Chuỗi gõ phải đúng hoa/thường (.tie5Roanl, R hoa) + Enter.

    keyguard.features chuẩn hóa phím về chữ thường nên không tự phân biệt được; kiểm tra ở đây,
    chỉ dựa trên sự kiện 'down' (khi nhả phím Shift trước, keyup của 'R' có thể thành 'r').
    """
    typed: list[str] = []
    open_keys: set[str] = set()
    for ev in sorted(events, key=lambda e: float(e["t"])):
        key = str(ev["key"])
        low = key.lower()
        if low in MODIFIER_KEYS:
            continue
        etype = str(ev["type"]).lower()
        if etype in ("down", "keydown"):
            if low in open_keys:  # auto-repeat
                continue
            open_keys.add(low)
            typed.append("enter" if low in ("enter", "return") else key)
        else:
            open_keys.discard("enter" if low == "return" else low)
    if typed != EXPECTED_DOWN_KEYS:
        shown = "".join("⏎" if c == "enter" else c for c in typed)
        raise InvalidSampleError(f"Chuỗi gõ {shown!r} không khớp {PHRASE!r} + Enter (phân biệt hoa/thường)")


def validate_events(events) -> list[dict]:
    """Kiểm tra một lần gõ; ném InvalidSampleError nếu sai cấu trúc hoặc sai câu mẫu."""
    if not isinstance(events, list) or not events:
        raise InvalidSampleError("Lần gõ phải là danh sách sự kiện phím không rỗng")
    if len(events) > MAX_EVENTS_PER_SAMPLE:
        raise InvalidSampleError("Lần gõ có quá nhiều sự kiện")
    clean = []
    for ev in events:
        if not isinstance(ev, dict) or not all(k in ev for k in ("key", "type", "t")):
            raise InvalidSampleError("Mỗi sự kiện phím cần có key, type và t")
        if isinstance(ev["t"], bool) or not isinstance(ev["t"], (int, float)) or not math.isfinite(ev["t"]):
            raise InvalidSampleError("Thời điểm t của sự kiện phím không hợp lệ")
        if not isinstance(ev["key"], str) or not isinstance(ev["type"], str):
            raise InvalidSampleError("key và type của sự kiện phím phải là chuỗi")
        clean.append({"key": ev["key"], "type": ev["type"], "t": float(ev["t"])})
    check_case(clean)
    feats = extract_features(clean)
    if len(feats) != 31 or not np.all(np.isfinite(feats)):
        raise InvalidSampleError("Không trích được đặc trưng hợp lệ từ lần gõ")
    return clean


def parse_participant_id(value) -> str:
    if not isinstance(value, str) or not PARTICIPANT_RE.fullmatch(value):
        raise ApiError("Mã người tham gia không hợp lệ (dạng P01, P02, ...).", 400)
    return value


def normalize_username(value) -> tuple[str, str]:
    """Trả về (tên hiển thị, khóa so khớp không phân biệt hoa/thường)."""
    if not isinstance(value, str):
        raise ApiError("Vui lòng nhập tên tài khoản.", 400)
    display = " ".join(unicodedata.normalize("NFC", value).split())
    if not display:
        raise ApiError("Vui lòng nhập tên tài khoản.", 400)
    if len(display) > USERNAME_MAX_LEN:
        raise ApiError(f"Tên tài khoản tối đa {USERNAME_MAX_LEN} ký tự.", 400)
    if any(unicodedata.category(c).startswith("C") for c in display):
        raise ApiError("Tên tài khoản chứa ký tự không hợp lệ.", 400)
    return display, display.casefold()


# ----------------------------------------------------------------------------------------
# Thu dữ liệu
# ----------------------------------------------------------------------------------------
def collected_file(pid: str) -> Path:
    return safe_path(COLLECTED_DIR, f"{pid}.jsonl")


def read_records(pid: str) -> list[dict]:
    path = collected_file(pid)
    records = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except ValueError:
                    continue
    return records


def session_counts(pid: str) -> dict[str, int]:
    counts = {str(s): 0 for s in range(1, MAX_SESSIONS + 1)}
    for r in read_records(pid):
        key = str(r.get("session"))
        if key in counts:
            counts[key] += 1
    return counts


def known_participant_ids(registry: dict) -> set[str]:
    ids = set(registry)
    for f in COLLECTED_DIR.glob("P*.jsonl"):
        if PARTICIPANT_RE.fullmatch(f.stem):
            ids.add(f.stem)
    return ids


def reserve_participant_id() -> str:
    with data_lock():
        registry = read_json(PARTICIPANTS_FILE, {})
        ids = known_participant_ids(registry)
        nums = [int(i[1:]) for i in ids]
        pid = f"P{(max(nums) + 1 if nums else 1):02d}"
        registry[pid] = {"created_at": now_iso()}
        write_json_atomic(PARTICIPANTS_FILE, registry)
    return pid


# ----------------------------------------------------------------------------------------
# Tài khoản demo
# ----------------------------------------------------------------------------------------
def profile_file(profile_id: str) -> Path:
    if not PROFILE_ID_RE.fullmatch(profile_id):
        raise ApiError("Hồ sơ không hợp lệ.", 500)
    return safe_path(PROFILES_DIR, f"{profile_id}.json")


def find_account(accounts: dict, key: str) -> dict:
    acc = accounts.get(key)
    if not acc:
        raise ApiError("Tài khoản không tồn tại trong hệ thống!", 404)
    return acc


def apply_update(profile_id: str, events: list[dict]) -> None:
    """Đọc hồ sơ, gọi update() của TV1 với lần gõ đã được xác nhận, ghi lại. Gọi trong data_lock."""
    path = profile_file(profile_id)
    profile = read_json(path, None)
    if profile is None:
        raise ApiError("Không tìm thấy hồ sơ nhịp gõ của tài khoản.", 404)
    write_json_atomic(path, update(profile, events))


def hash_otp(otp: str, salt: str) -> str:
    return hashlib.sha256((salt + otp).encode()).hexdigest()


def purge_challenges(challenges: dict) -> dict:
    now = time.time()
    return {cid: c for cid, c in challenges.items() if c["expires"] > now}


# ----------------------------------------------------------------------------------------
# Giao diện
# ----------------------------------------------------------------------------------------
@app.route("/")
def collector_page():
    return render_template("index.html", phrase=PHRASE, max_reps=MAX_REPS, max_sessions=MAX_SESSIONS)


@app.route("/register")
def register_page():
    return render_template("register.html", phrase=PHRASE, n_enroll=load_config()["n_enroll"])


@app.route("/login")
def login_page():
    return render_template("login.html", phrase=PHRASE)


# ----------------------------------------------------------------------------------------
# API thu dữ liệu
# ----------------------------------------------------------------------------------------
@app.route("/api/get-id", methods=["GET"])
def api_get_id():
    """Cấp (và giữ chỗ) một mã ẩn danh mới; hai lần gọi luôn cho hai mã khác nhau."""
    return jsonify({"participant_id": reserve_participant_id()})


@app.route("/api/participant/<pid>", methods=["GET"])
def api_participant(pid):
    """Tiến độ của một mã đã có, để người tham gia quay lại thu phiên ngày 2/3."""
    pid = parse_participant_id(pid)
    with data_lock():
        if pid not in known_participant_ids(read_json(PARTICIPANTS_FILE, {})):
            raise ApiError("Mã người tham gia không tồn tại.", 404)
        counts = session_counts(pid)
    return jsonify({"success": True, "participant_id": pid, "sessions": counts, "max_reps": MAX_REPS})


@app.route("/api/submit-sample", methods=["POST"])
def api_submit_sample():
    data = json_body()
    pid = parse_participant_id(data.get("participant_id"))
    try:
        session = int(data.get("session"))
    except (TypeError, ValueError):
        raise ApiError("Phiên gõ không hợp lệ.", 400)
    if not 1 <= session <= MAX_SESSIONS:
        raise ApiError(f"Phiên gõ phải từ 1 đến {MAX_SESSIONS}.", 400)

    try:
        events = validate_events(data.get("events"))
    except InvalidSampleError as e:
        raise ApiError(f"Lỗi nhịp gõ: {e}", 400)

    with data_lock():
        if pid not in known_participant_ids(read_json(PARTICIPANTS_FILE, {})):
            raise ApiError("Mã người tham gia chưa được cấp.", 404)
        count = session_counts(pid)[str(session)]
        if count >= MAX_REPS:
            raise ApiError(f"Phiên {session} đã đủ {MAX_REPS} mẫu.", 409, count=count)
        rep = count + 1  # server tự đánh số: không thể trùng (người, phiên, lần gõ)
        record = {
            "participant_id": pid,
            "session": session,
            "rep": rep,
            "collected_at": now_iso(),
            "events": events,
        }
        with open(collected_file(pid), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    log.info("Đã ghi mẫu %s phiên %s lần %s", pid, session, rep)
    return jsonify({"success": True, "message": "Đã lưu mẫu gõ thành công!", "rep": rep, "count": rep})


# ----------------------------------------------------------------------------------------
# API demo xác thực
# ----------------------------------------------------------------------------------------
@app.route("/api/check-username", methods=["GET"])
def api_check_username():
    display, key = normalize_username(request.args.get("username"))
    available = key not in read_json(ACCOUNTS_FILE, {})
    return jsonify({"success": True, "available": available, "username": display})


@app.route("/api/enroll", methods=["POST"])
def api_enroll():
    """Nhận `samples` (danh sách các lần gõ, mỗi lần là danh sách sự kiện) và tạo hồ sơ."""
    data = json_body()
    display, key = normalize_username(data.get("username"))
    samples = data.get("samples")
    if not isinstance(samples, list) or not all(isinstance(s, list) for s in samples):
        raise ApiError("`samples` phải là danh sách các lần gõ.", 400)
    cfg = load_config()
    if len(samples) < cfg["min_enroll"]:
        raise ApiError(f"Cần gõ đủ {cfg['min_enroll']} lần để đăng ký, mới có {len(samples)}.", 400)
    if len(samples) > MAX_ENROLL_SAMPLES:
        raise ApiError("Quá nhiều lần gõ.", 400)

    clean = []
    for i, s in enumerate(samples, 1):
        try:
            clean.append(validate_events(s))
        except InvalidSampleError as e:
            raise ApiError(f"Lần gõ thứ {i} không hợp lệ: {e}", 400)

    profile = enroll(clean, cfg)  # tính trước khi khóa để giữ khóa thật ngắn

    with data_lock():
        accounts = read_json(ACCOUNTS_FILE, {})
        if key in accounts:
            raise ApiError("Tên tài khoản đã tồn tại, vui lòng chọn tên khác.", 409)
        profile_id = uuid.uuid4().hex
        write_json_atomic(profile_file(profile_id), profile)
        accounts[key] = {"id": profile_id, "display": display, "created_at": now_iso()}
        write_json_atomic(ACCOUNTS_FILE, accounts)
    log.info("Đã tạo tài khoản %s (hồ sơ %s)", display, profile_id)
    return jsonify({"success": True, "message": f"Đăng ký tài khoản {display} thành công!"})


@app.route("/api/verify", methods=["POST"])
def api_verify():
    """Xác thực một lần gõ. Chấp nhận -> update hồ sơ. Không khớp -> tạo thử thách OTP mô phỏng."""
    data = json_body()
    _, key = normalize_username(data.get("username"))
    try:
        events = validate_events(data.get("events"))
    except InvalidSampleError as e:
        raise ApiError(f"Lỗi gõ sai câu mẫu: {e}", 400)

    accounts = read_json(ACCOUNTS_FILE, {})
    acc = find_account(accounts, key)
    profile = read_json(profile_file(acc["id"]), None)
    if profile is None:
        raise ApiError("Không tìm thấy hồ sơ nhịp gõ của tài khoản.", 404)

    confidence, accepted = verify(profile, events)
    confidence = float(confidence)
    if not math.isfinite(confidence):
        raise ApiError("Không tính được điểm tin cậy.", 500)

    if accepted:
        with data_lock():
            apply_update(acc["id"], events)
        return jsonify({
            "success": True, "accepted": True, "confidence": confidence, "otp_required": False,
            "message": "Đăng nhập thành công! Nhịp gõ khớp. Hồ sơ đã được cập nhật.",
        })

    # Không khớp: lần gõ này CHƯA được đưa vào hồ sơ, chỉ giữ trong thử thách chờ OTP.
    otp = f"{secrets.randbelow(10**6):06d}"
    salt = secrets.token_hex(8)
    cid = secrets.token_urlsafe(16)
    with data_lock():
        challenges = purge_challenges(read_json(CHALLENGES_FILE, {}))
        challenges[cid] = {
            "profile_id": acc["id"], "otp_hash": hash_otp(otp, salt), "salt": salt,
            "events": events, "attempts": 0, "expires": time.time() + OTP_TTL_SECONDS,
        }
        write_json_atomic(CHALLENGES_FILE, challenges)
    log.info("[OTP MÔ PHỎNG] tài khoản %s: %s (hiệu lực %d phút)", acc["display"], otp, OTP_TTL_SECONDS // 60)
    body = {
        "success": True, "accepted": False, "confidence": confidence, "otp_required": True,
        "challenge_id": cid, "otp_ttl_seconds": OTP_TTL_SECONDS, "max_attempts": OTP_MAX_ATTEMPTS,
        "message": "Nhịp gõ không khớp. Cần xác minh thêm bằng mã OTP.",
    }
    if SHOW_OTP_IN_RESPONSE:
        body["demo_otp"] = otp  # chỉ để mô phỏng tin nhắn SMS; server vẫn là bên kiểm tra OTP
    return jsonify(body)


@app.route("/api/verify-otp", methods=["POST"])
def api_verify_otp():
    data = json_body()
    cid, otp = data.get("challenge_id"), data.get("otp")
    if not isinstance(cid, str) or not isinstance(otp, str) or not otp.strip():
        raise ApiError("Thiếu mã xác minh hoặc OTP.", 400)
    otp = otp.strip()

    with data_lock():
        challenges = purge_challenges(read_json(CHALLENGES_FILE, {}))
        ch = challenges.get(cid)
        if ch is None:
            write_json_atomic(CHALLENGES_FILE, challenges)
            raise ApiError("OTP đã hết hạn hoặc không tồn tại. Vui lòng gõ lại để nhận mã mới.", 410)
        if hmac.compare_digest(hash_otp(otp, ch["salt"]), ch["otp_hash"]):
            del challenges[cid]
            write_json_atomic(CHALLENGES_FILE, challenges)
            apply_update(ch["profile_id"], ch["events"])
            return jsonify({"success": True, "verified": True,
                            "message": "Xác minh OTP thành công! Hồ sơ nhịp gõ đã được cập nhật."})
        ch["attempts"] += 1
        left = OTP_MAX_ATTEMPTS - ch["attempts"]
        if left <= 0:
            del challenges[cid]
        write_json_atomic(CHALLENGES_FILE, challenges)
    if left <= 0:
        raise ApiError("Nhập sai OTP quá số lần cho phép. Vui lòng gõ lại để nhận mã mới.", 429)
    raise ApiError(f"OTP không đúng. Còn {left} lần thử.", 401, attempts_left=left)


# ----------------------------------------------------------------------------------------
# Lỗi: /api/* luôn trả JSON thống nhất {success: false, message}
# ----------------------------------------------------------------------------------------
@app.errorhandler(ApiError)
def handle_api_error(e: ApiError):
    return jsonify({"success": False, "message": e.message, **e.extra}), e.status


@app.errorhandler(HTTPException)
def handle_http_error(e: HTTPException):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "message": e.description or e.name}), e.code
    return e


@app.errorhandler(Exception)
def handle_unexpected(e: Exception):
    log.exception("Lỗi hệ thống")
    if request.path.startswith("/api/"):
        msg = "Lỗi hệ thống"
        if isinstance(e, FileNotFoundError) and "model_config" in str(e):
            msg = "Lỗi hệ thống: thiếu models/model_config.json"
        return jsonify({"success": False, "message": msg}), 500
    raise e


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=5000)
