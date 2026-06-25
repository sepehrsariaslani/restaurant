import frappe
# Delete web route cache
frappe.cache().delete_keys('web_route')
frappe.cache().delete_key('web_routes')
print("Cache cleared")
