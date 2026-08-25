import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class RestaurantTableSession(Document):
    def before_insert(self):
        if not self.opened_at:
            self.opened_at = now_datetime()

    def validate(self):
        self._validate_active_session_uniqueness()
        self._normalize_timestamps()

    def on_update(self):
        self._sync_table_state()

    def on_trash(self):
        self._sync_table_state(force_empty=True)

    def _validate_active_session_uniqueness(self):
        if self.status != "active" or not self.table:
            return

        existing = frappe.db.get_value(
            "Restaurant Table Session",
            {
                "table": self.table,
                "status": "active",
                "name": ["!=", self.name],
            },
            "name",
        )
        if existing:
            frappe.throw(f"Table {self.table} already has an active session: {existing}")

    def _normalize_timestamps(self):
        if self.status == "closed":
            if not self.closed_at:
                self.closed_at = now_datetime()
        else:
            self.closed_at = None

    def _sync_table_state(self, force_empty=False):
        if not self.table or not frappe.db.exists("Restaurant Table", self.table):
            return

        if force_empty:
            active_name = frappe.db.get_value(
                "Restaurant Table Session",
                {
                    "table": self.table,
                    "status": "active",
                },
                "name",
            )
            if active_name:
                frappe.db.set_value(
                    "Restaurant Table",
                    self.table,
                    {"status": "occupied", "active_session": active_name},
                    update_modified=False,
                )
            else:
                frappe.db.set_value(
                    "Restaurant Table",
                    self.table,
                    {"status": "empty", "active_session": ""},
                    update_modified=False,
                )
            return

        if self.status == "active":
            frappe.db.set_value(
                "Restaurant Table",
                self.table,
                {"status": "occupied", "active_session": self.name},
                update_modified=False,
            )
            return

        active_name = frappe.db.get_value(
            "Restaurant Table Session",
            {
                "table": self.table,
                "status": "active",
            },
            "name",
        )
        if active_name:
            frappe.db.set_value(
                "Restaurant Table",
                self.table,
                {"status": "occupied", "active_session": active_name},
                update_modified=False,
            )
        else:
            frappe.db.set_value(
                "Restaurant Table",
                self.table,
                {"status": "empty", "active_session": ""},
                update_modified=False,
            )
