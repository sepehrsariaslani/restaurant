import re

with open('restaurant/api.py', 'r') as f:
    content = f.read()

canonical_logic = """
def _resolve_canonical_kitchen_status(so_name, has_restaurant_status=True):
    # 1. Check Delivery Note
    dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
    if dn_exists:
        return "closed"
    
    per_delivered = frappe.db.get_value("Sales Order", so_name, "per_delivered") or 0
    if per_delivered >= 100:
        return "closed"

    manual_status = "new"
    if has_restaurant_status:
        manual_status = frappe.db.get_value("Sales Order", so_name, "restaurant_status") or "new"

    # 2. Check Work Orders
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, fields=["status", "docstatus", "produced_qty", "qty"])
        if wos:
            all_draft = True
            all_completed = True
            any_in_progress = False
            
            for wo in wos:
                if wo.docstatus == 1:
                    all_draft = False
                    if wo.status == "Completed" or float(wo.produced_qty or 0) >= float(wo.qty or 0):
                        pass
                    else:
                        all_completed = False
                        any_in_progress = True
                else:
                    all_completed = False
                    
            if not all_draft:
                if all_completed:
                    return "ready"
                if any_in_progress:
                    return "preparing"
            
            # If all WOs are draft, rely on manual KDS status (operator intent)
            if manual_status in ["preparing", "ready"]:
                return manual_status
            return "new"
            
    # 3. Direct fulfillment (No BOM / No Work Order)
    if manual_status in ["preparing", "ready"]:
        return manual_status
        
    return "new"
"""

if "_resolve_canonical_kitchen_status" not in content:
    content = content.replace("def get_kitchen_display_orders", canonical_logic + "\n\n@frappe.whitelist()\ndef get_kitchen_display_orders")

# Now inject it into the loop
old_status_logic = """
        status = "new"
        if has_restaurant_status:
            status = frappe.db.get_value("Sales Order", so_name, "restaurant_status") or "new"
"""

new_status_logic = """
        status = _resolve_canonical_kitchen_status(so_name, has_restaurant_status)
"""

content = content.replace(old_status_logic, new_status_logic)

with open('restaurant/api.py', 'w') as f:
    f.write(content)
