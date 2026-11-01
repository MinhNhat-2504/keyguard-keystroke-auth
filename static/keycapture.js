/* Bắt nhịp gõ dùng chung cho /, /register, /login.
 *
 * Mỗi lần gõ là danh sách sự kiện {key, type: "down"|"up", t} với t = performance.now() (ms),
 * đúng định dạng keyguard/features.py cần. Lần gõ kết thúc SAU KHI nhả phím Enter, nên đủ
 * down/up của mọi phím kể cả Enter. Sai câu hoặc bị dán/kéo thả thì tự xóa và gõ lại từ đầu.
 */
(function () {
    function attachKeyCapture(input, targetString, onSample) {
        let events = [];
        let locked = false;

        function reset() {
            events = [];
            input.value = "";
        }

        input.addEventListener("keydown", (e) => {
            if (locked) { e.preventDefault(); return; }
            events.push({ key: e.key, type: "down", t: performance.now() });
        });

        input.addEventListener("keyup", (e) => {
            if (locked) return;
            events.push({ key: e.key, type: "up", t: performance.now() });
            if (e.key !== "Enter") return;

            const sample = events;
            const typed = input.value;
            reset();
            if (typed !== targetString) {
                onSample(null, "Gõ sai chuỗi, vui lòng gõ lại từ đầu rồi nhấn Enter.");
                return;
            }
            onSample(sample, null);
        });

        // Xóa hết nội dung (Ctrl+A rồi Delete...) thì bỏ luôn sự kiện đã ghi.
        input.addEventListener("input", () => { if (input.value === "") events = []; });
        ["paste", "drop"].forEach((name) =>
            input.addEventListener(name, (e) => { e.preventDefault(); events = []; input.value = ""; }));

        return {
            lock() { locked = true; input.disabled = true; },
            unlock(focus = true) {
                locked = false; input.disabled = false; reset();
                if (focus) input.focus();
            },
            reset,
        };
    }

    window.attachKeyCapture = attachKeyCapture;
})();
