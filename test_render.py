import frappe
import sys
sys.path.insert(0, '/home/frappe/frappe-bench/apps')
try:
    mod = frappe.get_module('restaurant.restaurant.www.management.builder_templates')
    ctx = {}
    result = mod.get_context(ctx)
    print("SUCCESS:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
