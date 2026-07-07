import re

from frappe.model.document import Document


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\u0600-\u06FF\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


class RestaurantMenuItem(Document):
    def validate(self):
        if not self.slug and self.title:
            self.slug = _slugify(self.title)
        self.slug = _slugify(self.slug)
