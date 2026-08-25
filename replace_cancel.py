import re

with open("restaurant/api.py", "r") as f:
    content = f.read()

old_func = """	def _cancel_and_delete(doctype, names):
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
				summary["errors"].append(f"Failed to clean {doctype} {name}: {str(e)}")"""

new_func = """	def _cancel_and_delete(doctype, names):
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
				
				# Only delete if it's draft, or if it's a custom log (like POS Log / Ticket)
				# For core ERPNext documents, safe to delete draft, but CANCEL only if submitted.
				if doc.docstatus == 0 or doctype in ["Restaurant Production Ticket", "Restaurant POS Payment Log"]:
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
					summary["cleaned_records"][doctype].append(f"{name} (Deleted)")
				else:
					summary["cleaned_records"][doctype].append(f"{name} (Cancelled)")
			except Exception as e:
				summary["errors"].append(f"Failed to clean {doctype} {name}: {str(e)}")"""

if old_func in content:
    content = content.replace(old_func, new_func)
    with open("restaurant/api.py", "w") as f:
        f.write(content)
    print("Replaced successfully")
else:
    print("Old func not found")
