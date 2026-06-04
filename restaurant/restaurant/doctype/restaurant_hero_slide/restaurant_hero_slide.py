import frappe
from frappe.model.document import Document


class RestaurantHeroSlide(Document):
    def validate(self):
        if not self.cta_label:
            self.cta_label = "مشاهده محصول"

        item_slug = (self._get_item_slug() or "").strip() if self.linked_item else ""

        if item_slug:
            self.cta_url = f"/restaurant/item/{item_slug}"
        elif not self.cta_url:
            self.cta_url = "/restaurant/menu"

    def _get_item_slug(self):
        try:
            return frappe.db.get_value("Item", self.linked_item, "restaurant_slug")
        except Exception:
            return ""
