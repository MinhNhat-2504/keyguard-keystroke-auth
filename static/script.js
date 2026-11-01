let currentParticipantId = "";
let currentRep = 1;
const MAX_REPS = 40;
let eventsLog = [];

const inputField = document.getElementById('targetInput');
const statusMsg = document.getElementById('statusMsg');
const sessionSelect = document.getElementById('sessionSelect');
const changeUserBtn = document.getElementById('changeUserBtn');

// 1. Hàm xin một mã ID mới từ server
async function fetchNewId() {
    try {
        let res = await fetch('/api/get-id');
        let data = await res.json();
        currentParticipantId = data.participant_id;
       
        const pidEl = document.getElementById('pid');
        if (pidEl) pidEl.innerText = currentParticipantId;
    } catch (err) {
        const pidEl = document.getElementById('pid');
        if (pidEl) pidEl.innerText = "Lỗi kết nối server!";
    }
}

// Khi mở trang lần đầu
window.addEventListener('DOMContentLoaded', async () => {
    await fetchNewId();
});

// Nút đổi sang người test mới trên cùng một máy
if (changeUserBtn) {
    changeUserBtn.addEventListener('click', async () => {
        if (confirm("Chuyển sang người test tiếp theo? Dữ liệu của người trước đã được lưu an toàn.")) {
            currentRep = 1;
            inputField.disabled = false;
            inputField.value = "";
            statusMsg.innerText = "";
            await fetchNewId();
        }
    });
}

// 2. Lắng nghe sự kiện bàn phím (down / up)
if (inputField) {
    inputField.addEventListener('keydown', (e) => {
        if (currentRep > MAX_REPS) return;
        eventsLog.push({
            key: e.key,
            type: "down",
            t: performance.now()
        });
    });

    inputField.addEventListener('keyup', (e) => {
        if (currentRep > MAX_REPS) return;
        eventsLog.push({
            key: e.key,
            type: "up",
            t: performance.now()
        });
        
        // Khi gõ xong câu mẫu và bấm Enter
        if (e.key === "Enter") {
            submitSample();
        }
    });
}

// 3. Gửi dữ liệu lần gõ về server Flask
async function submitSample() {
    if (currentRep > MAX_REPS) return;

    const currentSession = sessionSelect ? parseInt(sessionSelect.value) : 1;

    let payload = {
        participant_id: currentParticipantId,
        session: currentSession,
        rep: currentRep,
        events: eventsLog
    };

    try {
        let response = await fetch('/api/submit-sample', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        let result = await response.json();

        if (result.success) {
            currentRep++;
           
            if (currentRep > MAX_REPS) {
                inputField.disabled = true;
                inputField.placeholder = "Đã hoàn thành đủ 40 mẫu!";
                if (statusMsg) {
                    statusMsg.style.color = "blue";
                    statusMsg.innerText = `🎉 Tuyệt vời! Bạn đã hoàn thành đủ 40/40 mẫu của Phiên ${currentSession}. Cảm ơn bạn!`;
                }
            } else {
                if (statusMsg) {
                    statusMsg.style.color = "green";
                    statusMsg.innerText = `Lần gõ #${currentRep - 1} thành công! (Tiến độ: ${currentRep - 1}/${MAX_REPS})`;
                }
            }
            inputField.value = "";
        } else {
            if (statusMsg) {
                statusMsg.style.color = "red";
                statusMsg.innerText = `Gõ sai: ${result.message} (Vui lòng gõ lại từ đầu)`;
            }
            inputField.value = "";
        }
    } catch (err) {
        if (statusMsg) {
            statusMsg.style.color = "red";
            statusMsg.innerText = "Không thể kết nối đến server!";
        }
    }
    eventsLog = [];
}