import re

with open('restaurant/api.py', 'r') as f:
    content = f.read()

# Remove the pre-filter on restaurant_status because the canonical status might be totally different
old_filter = """
    filters = {"docstatus": 1}
    if has_restaurant_status:
        # Also fetch 'delivered' status so that the frontend can show it in 'closed' views if needed
        filters["restaurant_status"] = ["in", ["new", "confirmed", "preparing", "ready", "delivered"]]
    
    if date:
        filters["transaction_date"] = date
"""

new_filter = """
    filters = {"docstatus": 1}
    # We DO NOT pre-filter by restaurant_status anymore.
    # The canonical status will be resolved for each order based on actual ERPNext documents.
    # However, to avoid fetching thousands of old orders, we MUST rely on the date filter.
    
    if date:
        filters["transaction_date"] = date
    else:
        filters["transaction_date"] = frappe.utils.today()
        
    # Also ignore cancelled orders entirely from this query to save processing
    filters["status"] = ["not in", ["Cancelled"]]
"""

content = content.replace(old_filter, new_filter)

with open('restaurant/api.py', 'w') as f:
    f.write(content)
