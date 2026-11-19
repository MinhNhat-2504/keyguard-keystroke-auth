// One request ID per capture, retained for retries and reloads in the same tab.
const PENDING_KEY = 'keyguard_pending_sample_v1';
const retrySampleBtn = document.getElementById('retrySampleBtn');
let pendingSample = null;
let sendingSample = false;
let pendingStored = false;
try {
    const saved = JSON.parse(sessionStorage.getItem(PENDING_KEY) || 'null');
    if (saved && /^P\d{2,4}$/.test(saved.participant_id) && /^[0-9a-f]{32}$/.test(saved.request_id)
        && Number.isInteger(saved.session) && saved.session >= 1 && saved.session <= 3
        && validDevice(saved.device_id) && Array.isArray(saved.events) && saved.events.length <= 200) {
        pendingSample = saved;
        pendingStored = true;
    }
} catch (e) { /* có thể bị chặn bộ nhớ trình duyệt */ }

async function queueSample(events) {
    if (pendingSample || sendingSample) return;
    const device = deviceInput.value.trim();
    if (!validDevice(device)) {
        say('Nhập mã thiết bị trước khi lưu mẫu.', 'red'); deviceInput.focus(); return;
    }
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    const requestId = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
    pendingSample = {participant_id: currentParticipantId, session: currentSession(),
        device_id: device, events: events, request_id: requestId};
    try { sessionStorage.setItem(PENDING_KEY, JSON.stringify(pendingSample)); pendingStored = true; }
    catch (e) { pendingStored = false; }
    await sendPendingSample();
}

function clearPendingSample() {
    pendingSample = null;
    try { sessionStorage.removeItem(PENDING_KEY); } catch (e) { /* ID cũ vẫn an toàn khi gửi lại */ }
    pendingStored = false;
}

async function sendPendingSample() {
    if (!pendingSample || sendingSample) return;
    sendingSample = true;
    const payload = pendingSample;
    const key = String(payload.session);
    capture.lock(); setBusy(true); retrySampleBtn.disabled = true;
    try {
        for (let attempt = 0; attempt < 2; attempt++) {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 15000);
            try {
                const response = await fetch('/api/submit-sample', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload), signal: controller.signal
                });
                if (response.status >= 500 || response.status === 408 || response.status === 429) continue;
                const result = await response.json();
                if (response.ok && result.success) {
                    if (result.request_id !== payload.request_id || !Number.isInteger(result.count)
                        || !Number.isInteger(result.rep)) throw new Error('Chưa xác nhận đúng mẫu');
                    clearPendingSample(); counts[key] = result.count; refreshProgress();
                    if (counts[key] < MAX_REPS) say(result.replayed
                        ? `Đã xác nhận mẫu #${result.rep}; không lưu trùng. Phiên ${payload.session}: ${result.count}/${MAX_REPS} mẫu.`
                        : `Lần gõ #${result.rep} thành công! (Tiến độ phiên ${payload.session}: ${result.count}/${MAX_REPS})`, 'green');
                    return;
                }
                if (response.status === 409 && Array.isArray(result.issues)) {
                    say(result.message + ' Mẫu đang chờ được giữ lại để đối chiếu.', 'red'); return;
                }
                if ([400, 404, 409, 413, 415, 422].includes(response.status) && result.success === false) {
                    clearPendingSample();
                    if (Number.isInteger(result.count)) counts[key] = result.count;
                    refreshProgress(); say(result.message || 'Mẫu bị từ chối; vui lòng kiểm tra và gõ lại.', 'red');
                    return;
                }
            } catch (e) { /* mất phản hồi: dùng lại nguyên payload và request_id */ }
            finally { clearTimeout(timeout); }
        }
        say(pendingStored
            ? 'Chưa xác nhận được mẫu đã lưu. Bấm “Gửi lại mẫu đang chờ”; tải lại tab này vẫn giữ mã yêu cầu.'
            : 'Chưa xác nhận được mẫu đã lưu. Bấm “Gửi lại mẫu đang chờ”; trình duyệt không lưu được mẫu chờ, đừng tải lại hoặc đóng tab.', 'red');
    } finally {
        sendingSample = false;
        retrySampleBtn.hidden = !pendingSample; retrySampleBtn.disabled = false;
        setBusy(Boolean(pendingSample));
        if (pendingSample) capture.lock();
    }
}

async function restorePendingSample() {
    if (!pendingSample) return false;
    const saved = pendingSample;
    setBusy(true); sessionSelect.value = String(saved.session); deviceInput.value = saved.device_id;
    if (!await resumeId(saved.participant_id)) {
        currentParticipantId = saved.participant_id; pidEl.innerText = saved.participant_id;
    }
    await sendPendingSample();
    return true;
}

retrySampleBtn.addEventListener('click', sendPendingSample);
