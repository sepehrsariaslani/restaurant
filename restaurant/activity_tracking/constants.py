DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 60
DEFAULT_ACTIVE_WINDOW_MINUTES = 5
DEFAULT_IDLE_AFTER_MINUTES = 10
DEFAULT_SESSION_TIMEOUT_MINUTES = 15
DEFAULT_RETENTION_DAYS = 30
DEFAULT_MAX_EVENT_BATCH_SIZE = 100

STATUS_ACTIVE = "active"
STATUS_IDLE = "idle"

SESSION_OPEN = "active"
SESSION_CLOSED = "closed"
SESSION_TIMED_OUT = "timed_out"

EVENT_TYPES = {
    "mousemove",
    "keydown",
    "click",
    "visibilitychange",
    "route_change",
    "form_load",
    "list_view",
    "report_view",
    "heartbeat",
}

OUTPUT_DOCTYPES = (
    "Sales Invoice",
    "Purchase Invoice",
    "Payment Entry",
    "Journal Entry",
)

TRACKED_ROLES_DEFAULT = "Desk User\nSystem Manager\nHR Manager"
