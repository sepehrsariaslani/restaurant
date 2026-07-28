import frappe
from frappe.utils import get_build_version
frappe.init(site="restaurant")
frappe.connect()
print(get_build_version())
