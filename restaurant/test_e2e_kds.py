import frappe
from restaurant.api import get_kitchen_display_orders, update_kitchen_order_status, place_order

def run():
    print("--- Setting up KDS E2E Test ---")
    frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_enabled", 1)
    frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_submit_work_order", 1)
    frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_material_transfer", 1)
    frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_manufacture", 1)
    frappe.db.set_value("Restaurant Web Settings", None, "restaurant_auto_flow_create_delivery_note", 1)
    frappe.db.commit()

    print("\n[1] Creating a mixed order (assuming default items) ...")
    # For a real ERPNext instance, we just need ANY valid item.
    # We will pick the first available active menu item to avoid "item not found".
    menu_item = frappe.db.get_value("Item", {"is_stock_item": 1}, "name")
    if not menu_item:
        print("No stock item found. Cannot run E2E.")
        return

    res = place_order(
        customer_info={"name": "KDS E2E Test", "mobile": "09121234567"},
        order_type="dine_in",
        items=[{"item_code": menu_item, "qty": 1}],
        include_service_items=0
    )
    so_name = res["sales_order"]
    frappe.db.commit()
    print(f"Sales Order created: {so_name}")

    def inspect_order_state(stage):
        print(f"\n--- State after: {stage} ---")
        status_res = get_kitchen_display_orders(limit=10)
        orders = status_res.get("orders", [])
        order_kds = next((o for o in orders if o["name"] == so_name), None)
        print(f"KDS Resolver Status: {order_kds['status'] if order_kds else 'NOT IN ACTIVE BOARD'}")

        wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, fields=["name", "status", "docstatus", "qty", "produced_qty"])
        print(f"Work Orders: {wos}")

        for wo in wos:
            ses = frappe.get_all("Stock Entry", filters={"work_order": wo["name"]}, fields=["name", "stock_entry_type", "docstatus"])
            print(f"  Stock Entries for {wo['name']}: {ses}")

        dns = frappe.get_all("Delivery Note Item", filters={"against_sales_order": so_name}, fields=["parent", "docstatus"])
        print(f"Delivery Notes: {dns}")

    inspect_order_state("NEW (Initial)")

    print("\n[2] Triggering PREPARING ...")
    try:
        update_kitchen_order_status(so_name, "preparing")
        inspect_order_state("PREPARING")
    except Exception as e:
        print(f"Failed preparing: {e}")

    print("\n[3] Triggering READY ...")
    try:
        update_kitchen_order_status(so_name, "ready")
        inspect_order_state("READY")
    except Exception as e:
        print(f"Failed ready: {e}")

    print("\n[4] Triggering DELIVERED ...")
    try:
        update_kitchen_order_status(so_name, "delivered")
        inspect_order_state("DELIVERED")
    except Exception as e:
        print(f"Failed delivered: {e}")

