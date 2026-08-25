import re

with open('restaurant/api.py', 'r') as f:
    content = f.read()

content = content.replace(
    "@frappe.whitelist()\n\ndef _resolve_canonical_kitchen_status",
    "def _resolve_canonical_kitchen_status"
)

with open('restaurant/api.py', 'w') as f:
    f.write(content)
