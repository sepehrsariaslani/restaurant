(() => {
    const TRACKER_FLAG = "__restaurant_employee_activity_tracker";
    if (window[TRACKER_FLAG]) {
        return;
    }
    window[TRACKER_FLAG] = true;

    const HEARTBEAT_METHOD = "restaurant.activity_tracking.api.heartbeat";
    const CLOSE_SESSION_METHOD = "restaurant.activity_tracking.api.close_session";
    const DEFAULT_HEARTBEAT_SECONDS = 60;
    const ACTIVE_WINDOW_SECONDS = 5 * 60;
    const IDLE_WINDOW_SECONDS = 10 * 60;
    const MAX_QUEUED_EVENTS = 40;

    const state = {
        lastInteractionAt: Date.now(),
        lastMouseEventAt: 0,
        lastStatusHint: "active",
        heartbeatSeconds: DEFAULT_HEARTBEAT_SECONDS,
        heartbeatTimer: null,
        requestInFlight: false,
        events: [],
    };

    function canTrack() {
        if (typeof frappe === "undefined") {
            return false;
        }

        const user = (frappe.session && frappe.session.user) || "Guest";
        if (!user || user === "Guest") {
            return false;
        }

        return true;
    }

    function enqueueEvent(eventType, extras) {
        const payload = {
            event_type: eventType,
            ts: new Date().toISOString(),
        };

        if (extras && typeof extras === "object") {
            Object.assign(payload, extras);
        }

        state.events.push(payload);
        if (state.events.length > MAX_QUEUED_EVENTS) {
            state.events = state.events.slice(-MAX_QUEUED_EVENTS);
        }
    }

    function markInteraction(eventType) {
        state.lastInteractionAt = Date.now();

        if (eventType === "mousemove") {
            if (Date.now() - state.lastMouseEventAt < 15000) {
                return;
            }
            state.lastMouseEventAt = Date.now();
        }

        enqueueEvent(eventType);
    }

    function getRouteParts() {
        if (!frappe.get_route) {
            return [];
        }

        const parts = frappe.get_route();
        return Array.isArray(parts) ? parts : [];
    }

    function getContext() {
        const routeParts = getRouteParts();
        const route = (frappe.get_route_str && frappe.get_route_str()) || routeParts.join("/");

        let doctype = "";
        let docname = "";

        if (typeof cur_frm !== "undefined" && cur_frm && cur_frm.doctype && cur_frm.doc) {
            doctype = cur_frm.doctype;
            docname = cur_frm.doc.name || "";
        } else if (routeParts[0] === "Form") {
            doctype = routeParts[1] || "";
            docname = routeParts[2] || "";
        } else if (routeParts[0] === "List") {
            doctype = routeParts[1] || "";
        } else if (routeParts[0] === "query-report") {
            doctype = "Report";
            docname = routeParts[1] || "";
        }

        const loweredRoute = String(route || "").toLowerCase();
        const isPos =
            loweredRoute.includes("point-of-sale") ||
            loweredRoute.startsWith("point-of-sale") ||
            loweredRoute.includes("/pos") ||
            doctype === "POS Invoice";

        return {
            route,
            doctype,
            docname,
            is_pos: isPos ? 1 : 0,
        };
    }

    function getStatusHint() {
        const inactiveSeconds = Math.floor((Date.now() - state.lastInteractionAt) / 1000);

        if (inactiveSeconds >= IDLE_WINDOW_SECONDS) {
            state.lastStatusHint = "idle";
            return "idle";
        }

        if (inactiveSeconds <= ACTIVE_WINDOW_SECONDS) {
            state.lastStatusHint = "active";
            return "active";
        }

        return state.lastStatusHint;
    }

    function flushHeartbeat(force) {
        if (!canTrack()) {
            return;
        }

        if (state.requestInFlight) {
            return;
        }

        if (!force && document.visibilityState === "hidden") {
            return;
        }

        state.requestInFlight = true;

        const payload = {
            client_ts: new Date().toISOString(),
            status_hint: getStatusHint(),
            inactive_seconds: Math.floor((Date.now() - state.lastInteractionAt) / 1000),
            events: state.events.slice(0),
            ...getContext(),
        };

        state.events = [];

        frappe.call({
            method: HEARTBEAT_METHOD,
            type: "POST",
            args: {
                payload: JSON.stringify(payload),
            },
            callback: (response) => {
                const message = response && response.message;
                if (message && message.next_interval_sec) {
                    const nextSeconds = Math.max(parseInt(message.next_interval_sec, 10) || DEFAULT_HEARTBEAT_SECONDS, 20);
                    if (nextSeconds !== state.heartbeatSeconds) {
                        state.heartbeatSeconds = nextSeconds;
                        restartHeartbeatLoop();
                    }
                }
            },
            error: () => {
                const returnedEvents = Array.isArray(payload.events) ? payload.events : [];
                state.events = returnedEvents.concat(state.events).slice(-MAX_QUEUED_EVENTS);
            },
            always: () => {
                state.requestInFlight = false;
            },
        });
    }

    function startHeartbeatLoop() {
        if (state.heartbeatTimer) {
            clearInterval(state.heartbeatTimer);
        }

        state.heartbeatTimer = setInterval(() => {
            flushHeartbeat(false);
        }, state.heartbeatSeconds * 1000);
    }

    function restartHeartbeatLoop() {
        startHeartbeatLoop();
    }

    function closeSession() {
        if (!canTrack()) {
            return;
        }

        try {
            frappe.call({
                method: CLOSE_SESSION_METHOD,
                type: "POST",
                args: {
                    reason: "tab_close",
                },
            });
        } catch (error) {
            // Ignore errors during unload.
        }
    }

    function boot() {
        if (!canTrack()) {
            return;
        }

        document.addEventListener("mousemove", () => markInteraction("mousemove"));
        document.addEventListener("keydown", () => markInteraction("keydown"));
        document.addEventListener("click", () => markInteraction("click"));

        document.addEventListener("visibilitychange", () => {
            enqueueEvent("visibilitychange", {
                meta: {
                    hidden: document.visibilityState === "hidden" ? 1 : 0,
                },
            });

            if (document.visibilityState === "visible") {
                state.lastInteractionAt = Date.now();
                flushHeartbeat(true);
            }
        });

        if (frappe.router && frappe.router.on) {
            frappe.router.on("change", () => {
                markInteraction("route_change");
                flushHeartbeat(true);
            });
        }

        window.addEventListener("beforeunload", closeSession);

        enqueueEvent("heartbeat", {
            meta: {
                boot: 1,
            },
        });

        flushHeartbeat(true);
        startHeartbeatLoop();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", boot);
    } else {
        boot();
    }
})();
