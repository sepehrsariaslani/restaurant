import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class RestaurantTableRequest(Document):
    def before_insert(self):
        if not self.created_at:
            self.created_at = now_datetime()

    def validate(self):
        self._validate_session_table()
        self._sync_resolved_at()

    def _validate_session_table(self):
        if not self.session or not self.table:
            return

        session_table = frappe.db.get_value("Restaurant Table Session", self.session, "table")
        if session_table and session_table != self.table:
            frappe.throw("Table Session is not linked to the selected table.")

    def _sync_resolved_at(self):
        if self.status == "done" and not self.resolved_at:
            self.resolved_at = now_datetime()
        elif self.status != "done":
            self.resolved_at = None
