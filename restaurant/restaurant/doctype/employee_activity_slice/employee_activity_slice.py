from frappe.model.document import Document
from frappe.utils import get_datetime, getdate


class EmployeeActivitySlice(Document):
    def validate(self):
        if self.from_time and not self.slice_date:
            self.slice_date = getdate(self.from_time)

        if self.to_time and self.from_time:
            from_time = get_datetime(self.from_time)
            to_time = get_datetime(self.to_time)
            if to_time < from_time:
                self.to_time = self.from_time
                to_time = from_time
            self.duration_seconds = max(int((to_time - from_time).total_seconds()), 0)

        if not self.to_time:
            self.duration_seconds = 0
