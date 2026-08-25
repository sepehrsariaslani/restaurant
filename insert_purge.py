import re

with open("restaurant/api.py", "r") as f:
    content = f.read()

new_func = """
@frappe.whitelist()
def purge_management_pos_order(order_name):
	_ensure_management_access()
	if not order_name:
		frappe.throw(_("Order name is required."))

	so_name = _resolve_sales_order_name(order_name)
	if not so_name or not frappe.db.exists("Sales Order", so_name):
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	summary = {
		"cleaned_records": {},
		"errors": []
	}

	def _cancel_and_delete(doctype, names):
		if not names:
			return
		if doctype not in summary["cleaned_records"]:
			summary["cleaned_records"][doctype] = []
		
		for name in set(names):
			if not frappe.db.exists(doctype, name):
				continue
			try:
				doc = frappe.get_doc(doctype, name)
				if doc.docstatus == 1:
					doc.flags.ignore_permissions = True
					doc.cancel()
				
				# Delete draft or cancelled doc
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
				summary["cleaned_records"][doctype].append(name)
			except Exception as e:
				summary["errors"].append(f"Failed to clean {doctype} {name}: {str(e)}")

	# 1. Gather dependent docs
	tickets = frappe.get_all("Restaurant Production Ticket", filters={"sales_order": so_name}, pluck="name", ignore_permissions=True) if frappe.db.exists("DocType", "Restaurant Production Ticket") else []
	
	wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, pluck="name", ignore_permissions=True) if frappe.db.exists("DocType", "Work Order") else []
	
	ses = []
	if wos and frappe.db.exists("DocType", "Stock Entry"):
		ses = frappe.get_all("Stock Entry", filters={"work_order": ["in", wos]}, pluck="name", ignore_permissions=True)
		
	dns = []
	if frappe.db.exists("DocType", "Delivery Note Item"):
		dn_items = frappe.get_all("Delivery Note Item", filters={"against_sales_order": so_name}, pluck="parent", ignore_permissions=True)
		dns = list(set(dn_items))
		
	sis = []
	if frappe.db.exists("DocType", "Sales Invoice Item"):
		si_items = frappe.get_all("Sales Invoice Item", filters={"sales_order": so_name}, pluck="parent", ignore_permissions=True)
		sis = list(set(si_items))
		
	pes = []
	if frappe.db.exists("DocType", "Payment Entry Reference"):
		refs = [{"reference_doctype": "Sales Order", "reference_name": so_name}]
		for si in sis:
			refs.append({"reference_doctype": "Sales Invoice", "reference_name": si})
			
		for ref in refs:
			pe_refs = frappe.get_all("Payment Entry Reference", filters=ref, pluck="parent", ignore_permissions=True)
			pes.extend(pe_refs)
		pes = list(set(pes))
		
	pos_logs = frappe.get_all("Restaurant POS Payment Log", filters={"sales_order": so_name}, pluck="name", ignore_permissions=True) if frappe.db.exists("DocType", "Restaurant POS Payment Log") else []

	# Cancel & Delete in dependency order
	_cancel_and_delete("Payment Entry", pes)
	_cancel_and_delete("Sales Invoice", sis)
	_cancel_and_delete("Delivery Note", dns)
	_cancel_and_delete("Stock Entry", ses)
	_cancel_and_delete("Work Order", wos)
	_cancel_and_delete("Restaurant Production Ticket", tickets)
	_cancel_and_delete("Restaurant POS Payment Log", pos_logs)
	
	# Finally Sales Order
	_cancel_and_delete("Sales Order", [so_name])

	frappe.db.commit()
	return {
		"status": "success",
		"order_name": so_name,
		"summary": summary
	}
"""

content = content.replace("def void_management_pos_order(order_name, reason=None):", new_func + "\n\n@frappe.whitelist()\ndef void_management_pos_order(order_name, reason=None):")

with open("restaurant/api.py", "w") as f:
    f.write(content)
print("Done")
