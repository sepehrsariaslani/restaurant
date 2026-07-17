import frappe
from restaurant.api import get_kitchen_display_orders, update_kitchen_order_status, place_order

frappe.init(site="restaurant")
frappe.connect()

# Setup settings
frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_enabled", 1)
frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_submit_work_order", 1)
frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_material_transfer", 1)
frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_manufacture", 1)
frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_create_delivery_note", 1)
frappe.db.commit()

# Create a SO
res = place_order(
    customer_info={"name": "Test KDS User", "mobile": "09121234567"},
    order_type="dine_in",
    items=[{"slug": "hot-dog", "qty": 1}],
    include_service_items=0
)
so_name = res["sales_order"]
print(f"Created SO: {so_name}")

# Check initial status
status = get_kitchen_display_orders(limit=10)
orders = status.get("orders", [])
order = next((o for o in orders if o["name"] == so_name), None)
print(f"Initial status: {order['status'] if order else 'NOT FOUND'}")

# Call update_kitchen_order_status to preparing
update_kitchen_order_status(so_name, "preparing")
status = get_kitchen_display_orders(limit=10)
order = next((o for o in status.get("orders", []) if o["name"] == so_name), None)
print(f"Status after preparing: {order['status'] if order else 'NOT FOUND'}")

wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, fields=["name", "status", "docstatus"])
print("Work Orders:", wos)
for wo in wos:
    ses = frappe.get_all("Stock Entry", filters={"work_order": wo["name"]}, fields=["name", "stock_entry_type", "docstatus"])
    print("Stock Entries for", wo["name"], ":", ses)

# Call update_kitchen_order_status to ready
update_kitchen_order_status(so_name, "ready")
status = get_kitchen_display_orders(limit=10)
order = next((o for o in status.get("orders", []) if o["name"] == so_name), None)
print(f"Status after ready: {order['status'] if order else 'NOT FOUND'}")

wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, fields=["name", "status", "docstatus"])
print("Work Orders:", wos)
for wo in wos:
    ses = frappe.get_all("Stock Entry", filters={"work_order": wo["name"]}, fields=["name", "stock_entry_type", "docstatus"])
    print("Stock Entries for", wo["name"], ":", ses)

# Call update_kitchen_order_status to delivered
update_kitchen_order_status(so_name, "delivered")
status = get_kitchen_display_orders(limit=10)
order = next((o for o in status.get("orders", []) if o["name"] == so_name), None)
print(f"Status after delivered: {order['status'] if order else 'NOT FOUND'}")

dns = frappe.get_all("Delivery Note Item", filters={"against_sales_order": so_name}, fields=["parent"])
print("Delivery Notes:", dns)

frappe.destroy()
