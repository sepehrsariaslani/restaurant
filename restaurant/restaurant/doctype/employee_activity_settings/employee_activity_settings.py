import frappe
from frappe.model.document import Document


class EmployeeActivitySettings(Document):
    def validate(self):
        self.heartbeat_interval_seconds = max(frappe.utils.cint(self.heartbeat_interval_seconds or 60), 20)
        self.active_window_minutes = max(frappe.utils.cint(self.active_window_minutes or 5), 1)
        self.idle_after_minutes = max(frappe.utils.cint(self.idle_after_minutes or 10), 2)
        self.session_timeout_minutes = max(frappe.utils.cint(self.session_timeout_minutes or 15), 5)
        self.raw_retention_days = max(frappe.utils.cint(self.raw_retention_days or 30), 1)
        self.max_event_batch_size = max(frappe.utils.cint(self.max_event_batch_size or 100), 10)

        if self.idle_after_minutes <= self.active_window_minutes:
            self.idle_after_minutes = self.active_window_minutes + 1
