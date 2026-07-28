import re

with open('restaurant/api.py', 'r') as f:
    api = f.read()

# 1. Update _start_kitchen_production
old_start = """def _start_kitchen_production(so_name):
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
                        frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "in_progress", update_modified=False)"""

new_start = """def _start_kitchen_production(so_name):
    # 1. Create tickets and Work Orders if they don't exist
    so_doc = frappe.get_doc("Sales Order", so_name)
    has_tickets = False
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        has_tickets = bool(frappe.db.exists("Restaurant Production Ticket", {"sales_order": so_name}))
        
    if not has_tickets:
        _create_production_for_sales_order(so_doc)

    # 2. Submit Work Orders and optionally do Material Transfer
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name})
        settings = _production_auto_settings()
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            # Submit if draft
            if settings.get("submit_work_order") and wo_doc.docstatus == 0:
                wo_doc.flags.ignore_permissions = True
                wo_doc.submit()
            
            # Material Transfer (Start production)
            wo_doc = frappe.get_doc("Work Order", wo.name)
            if wo_doc.docstatus == 1:
                pending_transfer = max(float(wo_doc.qty or 0) - float(wo_doc.material_transferred_for_manufacturing or 0), 0)
                if settings.get("material_transfer") and pending_transfer > 0 and not int(wo_doc.skip_transfer or 0):
                    _create_work_order_stock_entry(wo.name, "Material Transfer for Manufacture", pending_transfer, submit_doc=settings.get("submit_stock_entries"))
                
                # Mark ticket in_progress
                if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                    tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                    for t in tickets:
                        frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "in_progress", update_modified=False)"""

if old_start in api:
    api = api.replace(old_start, new_start)

# 2. Update _complete_kitchen_production
old_complete = """def _complete_kitchen_production(so_name):
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
                    frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "completed", update_modified=False)"""

new_complete = """def _complete_kitchen_production(so_name):
    settings = _production_auto_settings()
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name, "docstatus": 1})
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            pending_manufacture = max(float(wo_doc.qty or 0) - float(wo_doc.produced_qty or 0), 0)
            if settings.get("manufacture") and pending_manufacture > 0:
                _create_work_order_stock_entry(wo.name, "Manufacture", pending_manufacture, submit_doc=settings.get("submit_stock_entries"))
            
            # Mark ticket completed
            if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                for t in tickets:
                    frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "completed", update_modified=False)"""

if old_complete in api:
    api = api.replace(old_complete, new_complete)

# 3. Update update_kitchen_order_status
old_update = """    if _has_column("Sales Order", "restaurant_status"):
        _set_restaurant_order_status(so_name, status, force=True)
    
    # Update production tickets
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        tickets = frappe.get_all("Restaurant Production Ticket",
            filters={"sales_order": so_name},
            pluck="name",
            ignore_permissions=True
        )
        for ticket_name in tickets:
            ticket = frappe.get_doc("Restaurant Production Ticket", ticket_name)
            if status == "ready":
                ticket.db_set("status", "completed", update_modified=False)
            elif status == "preparing":
                ticket.db_set("status", "in_progress", update_modified=False)
    
    _append_sales_order_note(so_name, f"[KITCHEN] Status changed to: {status}")
    frappe.db.commit()
    
    # Stage-aware action flows
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
        pass
        
    return {"status": "success"}"""

new_update = """    # Execute strictly stage-separated backend action flows FIRST
    # If they fail, they will raise an exception and rollback.
    if status == "preparing":
        _start_kitchen_production(so_name)
    elif status == "ready":
        _complete_kitchen_production(so_name)
    elif status == "delivered":
        if frappe.db.exists("DocType", "Delivery Note"):
            dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
            if not dn_exists:
                _create_delivery_note_for_sales_order(so_name, submit_doc=True)

    # If backend actions succeeded, update the manual status texts
    if _has_column("Sales Order", "restaurant_status"):
        _set_restaurant_order_status(so_name, status, force=True)
    
    # Update production tickets loosely associated without WO
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        tickets = frappe.get_all("Restaurant Production Ticket",
            filters={"sales_order": so_name},
            pluck="name",
            ignore_permissions=True
        )
        for ticket_name in tickets:
            ticket = frappe.get_doc("Restaurant Production Ticket", ticket_name)
            if status == "ready":
                ticket.db_set("status", "completed", update_modified=False)
            elif status == "preparing":
                ticket.db_set("status", "in_progress", update_modified=False)
    
    _append_sales_order_note(so_name, f"[KITCHEN] Status changed to: {status}")
    frappe.db.commit()
        
    return {"status": "success"}"""

if old_update in api:
    api = api.replace(old_update, new_update)

with open('restaurant/api.py', 'w') as f:
    f.write(api)

print("Backend final stage separation applied.")
