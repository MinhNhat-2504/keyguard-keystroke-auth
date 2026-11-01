from flask import Flask, render_template, request, jsonify
from pathlib import Path
import json
import sys

# 1. Sửa thành .parent (1 cấp) để trỏ ĐÚNG vào thư mục gốc CODE hiện tại
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from keyguard.features import extract_features, InvalidSampleError
from keyguard.model import enroll, verify

app = Flask(__name__, template_folder="templates", static_folder="static")

# 2. Định nghĩa chính xác đường dẫn thư mục data nằm ở gốc project
COLLECTED_DIR = ROOT / "data" / "collected"
COLLECTED_DIR.mkdir(parents=True, exist_ok=True)

PROFILES_DIR = ROOT / "data" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

def get_next_participant_id():
    """Tự động quét các file cũ trong data/collected/ để cấp phát ID tiếp theo (P01, P02...)"""
    existing_files = list(COLLECTED_DIR.glob("P*.jsonl"))
    if not existing_files:
        return "P01"
   
    max_id = 0
    for f in existing_files:
        try:
            num_str = f.stem[1:]
            num = int(num_str)
            if num > max_id:
                max_id = num
        except ValueError:
            continue
    return f"P{max_id + 1:02d}"

# --- CÁC ROUTE GIAO DIỆN (FRONTEND) ---
@app.route('/')
def collector_page():
    """Trang thu thập dữ liệu (index.html)"""
    return render_template('index.html')

@app.route('/register')
def register_page():
    """Trang Web Demo: Đăng ký tài khoản mới"""
    return render_template('register.html')

@app.route('/login')
def login_page():
    """Trang Web Demo: Đăng nhập xác thực nhịp gõ"""
    return render_template('login.html')

# --- CÁC API CHO THU THẬP DỮ LIỆU ---
@app.route('/api/get-id', methods=['GET'])
def api_get_id():
    new_id = get_next_participant_id()
    return jsonify({"participant_id": new_id})

@app.route('/api/submit-sample', methods=['POST'])
def api_submit_sample():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Không nhận được dữ liệu gửi lên!"}), 400

    participant_id = data.get('participant_id')
    session = data.get('session', 1)
    rep = data.get('rep', 1)
    events = data.get('events')

    if not participant_id or not events:
        return jsonify({"success": False, "message": "Thiếu thông tin dữ liệu!"}), 400

    try:
        extract_features(events)

        # Ghi dữ liệu vào đúng file JSONL trong thư mục data/collected/
        file_path = COLLECTED_DIR / f"{participant_id}.jsonl"
        record = {
            "participant_id": participant_id,
            "session": int(session),
            "rep": int(rep),
            "events": events
        }
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"--> [THÀNH CÔNG] Đã ghi mẫu cho {participant_id} vào file: {file_path}")
        return jsonify({"success": True, "message": "Đã lưu mẫu gõ thành công!"})

    except InvalidSampleError as e:
        print(f"--> [LỖI MẪU GÕ]: {str(e)}")
        return jsonify({"success": False, "message": f"Lỗi nhịp gõ: {str(e)}"}), 400
    except Exception as e:
        print(f"--> [LỖI HỆ THỐNG]: {str(e)}")
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500

@app.route('/api/enroll', methods=['POST'])
def api_enroll():
    """API nhận danh sách các mẫu gõ để tạo hồ sơ (profile) cho user"""
    data = request.get_json()
    username = data.get('username')
    samples_events = data.get('samples', [])
    if not username or len(samples_events) < 5:
        return jsonify({"success": False, "message": "Vui lòng nhập tên tài khoản và gõ đủ số mẫu tối thiểu!"}), 400
    try:
        profile = enroll(samples_events)
        profile_path = PROFILES_DIR / f"{username}.json"
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
           
        return jsonify({"success": True, "message": f"Đăng ký tài khoản {username} thành công!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi tạo hồ sơ: {str(e)}"}), 500

@app.route('/api/verify', methods=['POST'])
def api_verify():
    """API nhận sự kiện gõ phím khi đăng nhập để xác thực"""
    data = request.get_json()
    username = data.get('username')
    events = data.get('events')
    if not username or not events:
        return jsonify({"success": False, "message": "Thiếu thông tin đăng nhập!"}), 400
    profile_path = PROFILES_DIR / f"{username}.json"
    if not profile_path.exists():
        return jsonify({"success": False, "message": "Tài khoản không tồn tại trong hệ thống!"}), 404
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        confidence, accepted = verify(profile, events)
        return jsonify({
            "success": True,
            "accepted": accepted,
            "confidence": float(confidence),
            "message": "Đăng nhập thành công! Nhịp gõ khớp." if accepted else "Đăng nhập thất bại! Nhịp gõ không khớp."
        })
    except InvalidSampleError as e:
        return jsonify({"success": False, "message": f"Lỗi gõ sai câu mẫu: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)