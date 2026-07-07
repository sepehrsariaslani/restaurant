import json

from frappe.model.document import Document


class EmployeeActivityEvent(Document):
    def validate(self):
        event_type = (self.event_type or "").strip().lower()
        self.event_type = event_type

        if self.meta_json:
            try:
                parsed = json.loads(self.meta_json)
                self.meta_json = json.dumps(parsed, ensure_ascii=True)
            except Exception:
                self.meta_json = "{}"
