import re

with open('restaurant/api.py', 'r') as f:
    content = f.read()

old_update = """
    _append_sales_order_note(so_name, f"[KITCHEN] Status changed to: {status}")
    frappe.db.commit()
    return {"status": "success"}
"""

new_update = """
    _append_sales_order_note(so_name, f"[KITCHEN] Status changed to: {status}")
    frappe.db.commit()
    
    # Actually trigger the canonical production flow so ERPNext documents reflect the real status
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
        pass
        
    return {"status": "success"}
"""

content = content.replace(old_update, new_update)

with open('restaurant/api.py', 'w') as f:
    f.write(content)
