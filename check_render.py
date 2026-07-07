import frappe
from restaurant.restaurant.www.management.builder_templates import get_context
ctx = {}
try:
    result = get_context(ctx)
    print("SUCCESS:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
