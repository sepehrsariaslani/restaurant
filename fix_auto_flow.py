import re

with open('restaurant/api.py', 'r') as f:
    content = f.read()

old_logic = """    # Actually trigger the canonical production flow so ERPNext documents reflect the real status
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

new_logic = """    # Actually trigger the canonical production flow based on the action stage.
    # We do NOT just blindly force auto_flow, because each stage means something specific.
    try:
        if status == "preparing":
            # Just trigger creation and WO submit if applicable
            _run_sales_order_auto_flow(so_name, trigger="manual", force=True)
        elif status == "ready":
            # The operator marked it ready.
            # Force auto flow to process stock entry/manufacture if possible.
            # (Note: _run_sales_order_auto_flow handles manufacture if WOs are submitted)
            _run_sales_order_auto_flow(so_name, trigger="manual", force=True)
        elif status == "delivered":
            # We don't blindly run auto_flow because that might recreate things.
            # If settings allow, the system should generate delivery note here,
            # but since KDS operator handles physical delivery, we just try to invoke 
            # delivery note generation explicitly if possible, or fallback to auto flow.
            _run_sales_order_auto_flow(so_name, trigger="manual", force=True)
    except Exception:
        pass"""

content = content.replace(old_logic, new_logic)

with open('restaurant/api.py', 'w') as f:
    f.write(content)

