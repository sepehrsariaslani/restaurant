import frappe

def get_dependent_docs(so_name):
    # 1. Tickets
    tickets = frappe.get_all("Restaurant Production Ticket", filters={"sales_order": so_name}, pluck="name")
    
    # 2. Work Orders
    wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, pluck="name")
    
    # 3. Stock Entries linked to these Work Orders
    ses = []
    if wos:
        ses = frappe.get_all("Stock Entry", filters={"work_order": ["in", wos]}, pluck="name")
        
    # 4. Delivery Notes linked to Sales Order
    dns = frappe.get_all("Delivery Note Item", filters={"against_sales_order": so_name}, pluck="parent")
    dns = list(set(dns))
    
    # 5. Sales Invoices linked to Sales Order
    sis = frappe.get_all("Sales Invoice Item", filters={"sales_order": so_name}, pluck="parent")
    sis = list(set(sis))
    
    # 6. Payment Entries linked to Sales Invoices or Sales Order
    pes = []
    refs = [{"reference_doctype": "Sales Order", "reference_name": so_name}]
    for si in sis:
        refs.append({"reference_doctype": "Sales Invoice", "reference_name": si})
        
    for ref in refs:
        pe_refs = frappe.get_all("Payment Entry Reference", filters=ref, pluck="parent")
        pes.extend(pe_refs)
    pes = list(set(pes))
    
    # 7. POS Payment Logs
    pos_logs = frappe.get_all("Restaurant POS Payment Log", filters={"sales_order": so_name}, pluck="name")
    
    return {
        "Payment Entry": pes,
        "Sales Invoice": sis,
        "Delivery Note": dns,
        "Stock Entry": ses,
        "Work Order": wos,
        "Restaurant Production Ticket": tickets,
        "Restaurant POS Payment Log": pos_logs,
        "Sales Order": [so_name]
    }

print("Loaded")
