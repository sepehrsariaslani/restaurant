import re

# 1. ManagementLayout.vue
layout_path = 'frontend/src/components/management/ManagementLayout.vue'
with open(layout_path, 'r') as f:
    layout = f.read()

layout = layout.replace(
    'const isKitchenPage = computed(() => props.page === "kitchen");',
    'const isKitchenPage = computed(() => props.page === "management-kitchen");'
)

with open(layout_path, 'w') as f:
    f.write(layout)


# 2. api.py
api_path = 'restaurant/api.py'
with open(api_path, 'r') as f:
    api = f.read()

old_filters = """    filters = {"docstatus": 1}
    if has_restaurant_status:
        # Also fetch 'delivered' status so that the frontend can show it in 'closed' views if needed
        filters["restaurant_status"] = ["in", ["new", "confirmed", "preparing", "ready", "delivered"]]
    
    if date:
        filters["transaction_date"] = date"""

new_filters = """    # Canonical filter: no pre-filtering on restaurant_status
    filters = {"docstatus": 1, "status": ["!=", "Cancelled"]}
    
    if date:
        filters["transaction_date"] = date
    else:
        filters["transaction_date"] = frappe.utils.today()"""

api = api.replace(old_filters, new_filters)

old_trigger = """    # Actually trigger the canonical production flow so ERPNext documents reflect the real status
    try:
        if status == "preparing":
            # Just kicking the auto flow will submit WOs if settings allow
            _run_sales_order_auto_flow(so_name, trigger="manual", force=True)
        elif status == "ready":
            # Run it again to potentially manufacture if settings allow
            _run_sales_order_auto_flow(so_name, trigger="manual", force=True)
        elif status == "delivered":
            # If the KDS says delivered, it might not auto-create Delivery Note unless settings allow.
            # But we run auto flow anyway.
            _run_sales_order_auto_flow(so_name, trigger="manual", force=True)
    except Exception:
        pass"""

new_trigger = """    # Stage-aware action flows
    try:
        if status == "preparing":
            # Start production: submit Work Orders
            _run_sales_order_auto_flow(so_name, trigger="manual", force=True)
        elif status == "ready":
            # Complete production: manufacture Work Orders
            if frappe.db.exists("DocType", "Work Order"):
                wos = frappe.get_all("Work Order", filters={"sales_order": so_name, "docstatus": 1})
                for wo in wos:
                    wo_doc = frappe.get_doc("Work Order", wo.name)
                    pending = max(float(wo_doc.qty or 0) - float(wo_doc.produced_qty or 0), 0)
                    if pending > 0:
                        try:
                            _create_work_order_stock_entry(wo.name, "Manufacture", pending, submit_doc=True)
                        except Exception:
                            pass
        elif status == "delivered":
            # Handoff: create Delivery Note
            if frappe.db.exists("DocType", "Delivery Note"):
                dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
                if not dn_exists:
                    try:
                        _create_delivery_note_for_sales_order(so_name, submit_doc=True)
                    except Exception:
                        pass
    except Exception:
        pass"""

api = api.replace(old_trigger, new_trigger)

with open(api_path, 'w') as f:
    f.write(api)

print("Fixes applied successfully.")
