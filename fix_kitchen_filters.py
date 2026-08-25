with open('restaurant/api.py', 'r') as f:
    content = f.read()

old_filters = """    filters = {"docstatus": 1}
    if has_restaurant_status:
        # Also fetch 'delivered' status so that the frontend can show it in 'closed' views if needed
        filters["restaurant_status"] = ["in", ["new", "confirmed", "preparing", "ready", "delivered"]]
    
    if date:
        filters["transaction_date"] = date"""

new_filters = """    filters = {"docstatus": 1, "status": ["!=", "Cancelled"]}
    
    # DO NOT pre-filter on restaurant_status because canonical logic resolves it from documents.
    # Otherwise we miss orders that have Work Orders but a stale manual text status.
    
    if date:
        filters["transaction_date"] = date
    else:
        filters["transaction_date"] = frappe.utils.today()"""

content = content.replace(old_filters, new_filters)

with open('restaurant/api.py', 'w') as f:
    f.write(content)

