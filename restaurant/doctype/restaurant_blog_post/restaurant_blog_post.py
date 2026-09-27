import re

import frappe
from frappe import _
from frappe.model.document import Document


class RestaurantBlogPost(Document):
    def validate(self):
        route = re.sub(r"[^\w\u0600-\u06ff-]+", "-", (self.route or self.title or "").strip().lower(), flags=re.UNICODE)
        route = re.sub(r"-+", "-", route).strip("-")
        if not route:
            frappe.throw(_("شناسهٔ صفحه معتبر نیست."))
        self.route = route
        duplicate = frappe.db.exists("Restaurant Blog Post", {"route": route, "name": ["!=", self.name]})
        if duplicate:
            frappe.throw(_("این نشانی قبلاً برای یک مقاله استفاده شده است."))
        if self.is_published and not self.published_on:
            self.published_on = frappe.utils.now_datetime()
        if self.related_products:
            seen = set()
            for row in self.related_products:
                if row.item_code in seen:
                    frappe.throw(_("هر محصول فقط یک‌بار می‌تواند به مقاله اضافه شود."))
                seen.add(row.item_code)
