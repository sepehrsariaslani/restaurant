from frappe.model.document import Document
from frappe.utils import get_datetime


class EmployeeActivitySession(Document):
    def validate(self):
        if self.session_end and self.session_start:
            start = get_datetime(self.session_start)
            end = get_datetime(self.session_end)
            if end < start:
                self.session_end = self.session_start

        if self.session_start and self.session_end:
            duration = (get_datetime(self.session_end) - get_datetime(self.session_start)).total_seconds()
            self.online_seconds = max(int(duration), 0)

        if self.status == "active":
            self.session_end = None
