import frappe
from frappe import _
from frappe.model.document import Document


ALLOWED_STATES = {
	"Previewed",
	"Running",
	"Completed",
	"Completed With Blocks",
	"Failed",
}
TERMINAL_STATES = {"Completed", "Completed With Blocks", "Failed"}


class RestaurantWarehouseRecoveryRun(Document):
	def validate(self):
		if self.state not in ALLOWED_STATES:
			frappe.throw(_("وضعیت اجرای اصلاح انبار معتبر نیست."))

		if self.is_new():
			return

		old_state = frappe.db.get_value(self.doctype, self.name, "state")
		if old_state in TERMINAL_STATES and self.state != old_state:
			frappe.throw(_("اجرای نهایی‌شده قابل بازگشت به مرحلهٔ قبل نیست."))
		if old_state in TERMINAL_STATES and self.has_value_changed("summary_json"):
			frappe.throw(_("گزارش اجرای نهایی‌شده قابل تغییر نیست."))
