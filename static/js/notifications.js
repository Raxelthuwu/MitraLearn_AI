(function () {
    const btn = document.getElementById("notif-btn");
    if (!btn || !btn.dataset.pollUrl) {
        return;
    }

    const badge = document.getElementById("notif-badge");
    const POLL_MS = 8000;

    function updateBadge(count) {
        if (!badge) {
            return;
        }
        if (count > 0) {
            badge.textContent = String(count);
            badge.hidden = false;
        } else {
            badge.hidden = true;
        }
    }

    async function poll() {
        try {
            const response = await fetch(btn.dataset.pollUrl, {
                headers: { Accept: "application/json" },
                credentials: "same-origin",
            });
            if (!response.ok) {
                return;
            }
            const data = await response.json();
            updateBadge(data.unreadCount || 0);
            if (typeof window.updateNotificationList === "function") {
                window.updateNotificationList(data.notifications || []);
            }
        } catch (err) {
            // Ignore transient network errors during polling
        }
    }

    poll();
    setInterval(poll, POLL_MS);

    document.addEventListener("visibilitychange", function () {
        if (!document.hidden) {
            poll();
        }
    });
})();
