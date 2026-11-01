// Trang thu dữ liệu: mã người tham gia và số lần gõ mỗi phiên do SERVER quản lý.
// TARGET_STRING và MAX_REPS do server truyền qua thuộc tính data- của thẻ <body> trong index.html.
const TARGET_STRING = document.body.dataset.phrase;
const MAX_REPS = parseInt(document.body.dataset.maxReps, 10);
const STORAGE_KEY = "keyguard_participant_id";

let currentParticipantId = "";
let counts = { "1": 0, "2": 0, "3": 0 };   // số mẫu đã lưu của mã hiện tại, theo phiên

const inputField = document.getElementById('targetInput');
const statusMsg = document.getElementById('statusMsg');
const sessionSelect = document.getElementById('sessionSelect');
const changeUserBtn = document.getElementById('changeUserBtn');
const resumeBtn = document.getElementById('resumeBtn');
const resumeInput = document.getElementById('resumeInput');
const pidEl = document.getElementById('pid');
const progressInfo = document.getElementById('progressInfo');

let capture = null;

function say(text, color) {
    statusMsg.style.color = color || "";
    statusMsg.innerText = text;
}

function rememberPid(pid) {
    try { pid ? localStorage.setItem(STORAGE_KEY, pid) : localStorage.removeItem(STORAGE_KEY); } catch (e) { /* bỏ qua */ }
}

function recalledPid() {
    try { return localStorage.getItem(STORAGE_KEY) || ""; } catch (e) { return ""; }
}

function currentSession() {
    return parseInt(sessionSelect.value, 10) || 1;
}

// Cập nhật ô nhập và dòng tiến độ theo phiên đang chọn.
function refreshProgress(focus = true) {
    const s = currentSession();
    const n = counts[String(s)] || 0;
    progressInfo.innerText = currentParticipantId ? `Phiên ${s}: đã có ${n}/${MAX_REPS} mẫu` : "";
    if (!currentParticipantId) {
        capture.lock();
        return;
    }
    if (n >= MAX_REPS) {
        capture.lock();
        inputField.placeholder = `Phiên ${s} đã đủ ${MAX_REPS} mẫu!`;
        say(`🎉 Phiên ${s} đã hoàn thành đủ ${MAX_REPS}/${MAX_REPS} mẫu. Cảm ơn bạn! Chọn phiên khác nếu cần.`, "blue");
    } else {
        capture.unlock(focus);
        inputField.placeholder = "Bấm vào đây và bắt đầu gõ...";
        say("");
    }
}

function setParticipant(pid, sessionCounts) {
    currentParticipantId = pid;
    counts = Object.assign({ "1": 0, "2": 0, "3": 0 }, sessionCounts || {});
    pidEl.innerText = pid || "Lỗi kết nối server!";
    rememberPid(pid);
    refreshProgress();
}

// Xin mã mới (server giữ chỗ nên hai người cùng lúc không bao giờ trùng mã).
async function fetchNewId() {
    try {
        const res = await fetch('/api/get-id');
        const data = await res.json();
        if (!res.ok || !data.participant_id) throw new Error(data.message || "Lỗi");
        setParticipant(data.participant_id, {});
    } catch (err) {
        setParticipant("", {});
        say("Không thể xin mã từ server!", "red");
    }
}

// Quay lại với mã đã có để thu phiên ngày 2/3.
async function resumeId(pid) {
    try {
        const res = await fetch('/api/participant/' + encodeURIComponent(pid));
        const data = await res.json();
        if (!res.ok || !data.success) {
            say(data.message || "Không tìm thấy mã này.", "red");
            return false;
        }
        setParticipant(data.participant_id, data.sessions);
        return true;
    } catch (err) {
        say("Không thể kết nối đến server!", "red");
        return false;
    }
}

async function submitSample(events) {
    capture.lock();
    try {
        const response = await fetch('/api/submit-sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                participant_id: currentParticipantId,
                session: currentSession(),
                events: events
            })
        });
        const result = await response.json();
        const s = String(currentSession());

        if (response.ok && result.success) {
            counts[s] = result.count;
            refreshProgress();
            if (counts[s] < MAX_REPS) {
                say(`Lần gõ #${counts[s]} thành công! (Tiến độ: ${counts[s]}/${MAX_REPS})`, "green");
            }
        } else {
            if (typeof result.count === "number") counts[s] = result.count;
            refreshProgress();
            if (counts[s] < MAX_REPS) say(`Gõ sai: ${result.message} (Vui lòng gõ lại từ đầu)`, "red");
        }
    } catch (err) {
        capture.unlock();
        say("Không thể kết nối đến server! Lần gõ này chưa được lưu, hãy gõ lại.", "red");
    }
}

window.addEventListener('DOMContentLoaded', async () => {
    capture = attachKeyCapture(inputField, TARGET_STRING, (events, err) => {
        if (err) { say(err, "red"); return; }
        submitSample(events);
    });
    capture.lock();

    const saved = recalledPid();
    if (!(saved && await resumeId(saved))) await fetchNewId();
});

sessionSelect.addEventListener('change', () => refreshProgress(false));

changeUserBtn.addEventListener('click', async () => {
    if (confirm("Chuyển sang người test tiếp theo? Dữ liệu của người trước đã được lưu an toàn.")) {
        capture.reset();
        await fetchNewId();
    }
});

resumeBtn.addEventListener('click', async () => {
    const pid = resumeInput.value.trim().toUpperCase();
    if (!/^P\d{2,4}$/.test(pid)) { say("Mã không hợp lệ (dạng P01, P02, ...).", "red"); return; }
    capture.reset();
    if (await resumeId(pid)) resumeInput.value = "";
});
