import re

with open('restaurant/api.py', 'r') as f:
    api = f.read()

new_helpers = """
def _start_kitchen_production(so_name):
    # 1. Create tickets and Work Orders if they don't exist
    so_doc = frappe.get_doc("Sales Order", so_name)
    has_tickets = False
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        has_tickets = bool(frappe.db.exists("Restaurant Production Ticket", {"sales_order": so_name}))
        
    if not has_tickets:
        try:
            _create_production_for_sales_order(so_doc)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"KDS Ticket Create ({so_name})")

    # 2. Submit Work Orders and optionally do Material Transfer
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name})
        settings = _production_auto_settings()
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            # Submit if draft
            if settings.get("submit_work_order") and wo_doc.docstatus == 0:
                try:
                    wo_doc.flags.ignore_permissions = True
                    wo_doc.submit()
                except Exception:
                    continue
            
            # Material Transfer (Start production)
            wo_doc = frappe.get_doc("Work Order", wo.name)
            if wo_doc.docstatus == 1:
                pending_transfer = max(float(wo_doc.qty or 0) - float(wo_doc.material_transferred_for_manufacturing or 0), 0)
                if settings.get("material_transfer") and pending_transfer > 0 and not int(wo_doc.skip_transfer or 0):
                    try:
                        _create_work_order_stock_entry(wo.name, "Material Transfer for Manufacture", pending_transfer, submit_doc=settings.get("submit_stock_entries"))
                    except Exception:
                        pass
                
                # Mark ticket in_progress
                if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                    tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                    for t in tickets:
                        frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "in_progress", update_modified=False)

def _complete_kitchen_production(so_name):
    settings = _production_auto_settings()
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name, "docstatus": 1})
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            pending_manufacture = max(float(wo_doc.qty or 0) - float(wo_doc.produced_qty or 0), 0)
            if settings.get("manufacture") and pending_manufacture > 0:
                try:
                    _create_work_order_stock_entry(wo.name, "Manufacture", pending_manufacture, submit_doc=settings.get("submit_stock_entries"))
                except Exception:
                    pass
            
            # Mark ticket completed
            if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                for t in tickets:
                    frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "completed", update_modified=False)

"""

old_helpers = """
def _start_kitchen_production(so_name):
    # 1. Create tickets and Work Orders if they don't exist
    so_doc = frappe.get_doc("Sales Order", so_name)
    has_tickets = False
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        has_tickets = bool(frappe.db.exists("Restaurant Production Ticket", {"sales_order": so_name}))
        
    if not has_tickets:
        try:
            _create_production_for_sales_order(so_doc)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"KDS Ticket Create ({so_name})")

    # 2. Submit Work Orders and optionally do Material Transfer
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name})
        settings = _production_auto_settings()
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            # Submit if draft
            if wo_doc.docstatus == 0:
                try:
                    wo_doc.flags.ignore_permissions = True
                    wo_doc.submit()
                except Exception:
                    continue
            
            # Material Transfer (Start production)
            wo_doc = frappe.get_doc("Work Order", wo.name)
            if wo_doc.docstatus == 1:
                pending_transfer = max(float(wo_doc.qty or 0) - float(wo_doc.material_transferred_for_manufacturing or 0), 0)
                if pending_transfer > 0 and not int(wo_doc.skip_transfer or 0):
                    try:
                        _create_work_order_stock_entry(wo.name, "Material Transfer for Manufacture", pending_transfer, submit_doc=True)
                    except Exception:
                        pass
                
                # Mark ticket in_progress
                if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                    tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                    for t in tickets:
                        frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "in_progress", update_modified=False)

def _complete_kitchen_production(so_name):
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name, "docstatus": 1})
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            pending_manufacture = max(float(wo_doc.qty or 0) - float(wo_doc.produced_qty or 0), 0)
            if pending_manufacture > 0:
                try:
                    _create_work_order_stock_entry(wo.name, "Manufacture", pending_manufacture, submit_doc=True)
                except Exception:
                    pass
            
            # Mark ticket completed
            if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                for t in tickets:
                    frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "completed", update_modified=False)
"""

api = api.replace(old_helpers, new_helpers)

# For delivered:
old_delivered = """        elif status == "delivered":
            # Handoff: create Delivery Note
            if frappe.db.exists("DocType", "Delivery Note"):
                dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
                if not dn_exists:
                    try:
                        _create_delivery_note_for_sales_order(so_name, submit_doc=True)
                    except Exception:
                        pass"""

new_delivered = """        elif status == "delivered":
            # Handoff: create Delivery Note
            settings = _production_auto_settings()
            if settings.get("create_delivery_note") and frappe.db.exists("DocType", "Delivery Note"):
                dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
                if not dn_exists:
                    try:
                        _create_delivery_note_for_sales_order(so_name, submit_doc=True)
                    except Exception:
                        pass"""

api = api.replace(old_delivered, new_delivered)

with open('restaurant/api.py', 'w') as f:
    f.write(api)

print("Stage separation fully complete with settings.")
