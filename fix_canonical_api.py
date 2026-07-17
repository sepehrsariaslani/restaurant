import re

with open('restaurant/api.py', 'r') as f:
    api = f.read()

# We want to replace everything from `def _start_kitchen_production(so_name):` up to `return {"status": "success"}`

old_start_idx = api.find('def _start_kitchen_production(so_name):')
old_end_idx = api.find('return {"status": "success"}', old_start_idx) + len('return {"status": "success"}')

new_code = """def _start_kitchen_production(so_name):
    # 1. Create tickets and Work Orders if they don't exist
    so_doc = frappe.get_doc("Sales Order", so_name)
    has_tickets = False
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        has_tickets = bool(frappe.db.exists("Restaurant Production Ticket", {"sales_order": so_name}))
        
    if not has_tickets:
        _create_production_for_sales_order(so_doc)

    # 2. Submit Work Orders and do Material Transfer
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
                        frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "in_progress", update_modified=False)

def _complete_kitchen_production(so_name):
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
                    frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "completed", update_modified=False)

                    
@frappe.whitelist()
def get_kitchen_display_orders(limit=50, date=None):
    \"\"\"Get production-ready orders for kitchen display\"\"\"
    _ensure_management_access()
    limit = cint(limit) or 100
    orders = []
    
    if not frappe.db.exists("DocType", "Sales Order"):
        return {"orders": []}
    
    has_restaurant_status = _has_column("Sales Order", "restaurant_status")
    has_restaurant_note = _has_column("Sales Order Item", "restaurant_note")
    has_order_type = _has_column("Sales Order", "restaurant_order_type")
    has_prod_ticket = frappe.db.exists("DocType", "Restaurant Production Ticket")
    
    # Canonical filter: no pre-filtering on restaurant_status
    filters = {"docstatus": 1, "status": ["!=", "Cancelled"]}
    
    if date:
        filters["transaction_date"] = date
    else:
        filters["transaction_date"] = frappe.utils.today()
    
    so_fields = ["name", "customer_name", "customer", "transaction_date", "creation"]
    if has_order_type:
        so_fields.append("restaurant_order_type")
    
    rows = frappe.get_all("Sales Order",
        fields=so_fields,
        filters=filters,
        order_by="creation desc",
        limit=limit,
        ignore_permissions=True,
    )
    
    so_item_fields = ["item_code", "item_name", "qty", "rate", "description"]
    if has_restaurant_note:
        so_item_fields.append("restaurant_note")
    
    for so in rows:
        so_name = so.name
        items = []
        tickets = []
        
        so_items = frappe.get_all("Sales Order Item",
            fields=so_item_fields,
            filters={"parent": so_name},
            order_by="idx asc",
            ignore_permissions=True
        )
        for item in so_items:
            items.append({
                "item_code": item.item_code,
                "title": item.item_name,
                "description": item.description or "",
                "qty": flt(item.qty),
                "rate": flt(item.rate),
                "note": item.restaurant_note if has_restaurant_note else "",
            })
        
        if has_prod_ticket:
            tickets = frappe.get_all("Restaurant Production Ticket",
                fields=["name", "menu_item", "qty", "status", "work_order"],
                filters={"sales_order": so_name},
                ignore_permissions=True
            )
        
        status = _resolve_canonical_kitchen_status(so_name, has_restaurant_status)
        
        channel = so.restaurant_order_type if has_order_type else ""
        order_code = so_name
        
        orders.append({
            "name": so_name,
            "order_code": order_code,
            "customer_name": so.customer_name or "POS Customer",
            "status": status,
            "channel": channel or "حضوری",
            "items": items,
            "production_tickets": tickets,
            "creation": str(so.creation or ""),
            "created_at": str(so.transaction_date or so.creation or ""),
        })
    
    return {"orders": orders}


@frappe.whitelist()
def update_kitchen_order_status(order_name, status):
    \"\"\"Update kitchen order status\"\"\"
    _ensure_management_access()
    if not order_name or not status:
        frappe.throw(_("Order name and status are required."))
    
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)
    
    # 1. Execute strictly stage-separated canonical backend action flows FIRST.
    # If any underlying document creation/submission fails, it raises an exception 
    # which bubbles up and stops the UI from advancing incorrectly.
    if status == "preparing":
        _start_kitchen_production(so_name)
    elif status == "ready":
        _complete_kitchen_production(so_name)
    elif status == "delivered":
        if frappe.db.exists("DocType", "Delivery Note"):
            dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
            if not dn_exists:
                _create_delivery_note_for_sales_order(so_name, submit_doc=True)

    # 2. Only if the canonical documents succeeded (or no documents apply for this item),
    # update the manual text statuses for operator visibility.
    if _has_column("Sales Order", "restaurant_status"):
        _set_restaurant_order_status(so_name, status, force=True)
    
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

api = api[:old_start_idx] + new_code + api[old_end_idx:]

with open('restaurant/api.py', 'w') as f:
    f.write(api)

print("Canonical API fixed.")
