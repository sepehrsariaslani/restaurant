import frappe

items = frappe.get_all('Item', filters={'image': ['is', 'not set']}, fields=['name'], limit=1000)
fixed = 0
no_attach = 0

for item in items:
    if item.name.startswith('SNP-'):
        continue
    attachments = frappe.get_all('File', 
        filters={'attached_to_doctype': 'Item', 'attached_to_name': item.name}, 
        fields=['file_url'], 
        order_by='creation asc', 
        limit=1
    )
    if attachments and attachments[0].file_url:
        frappe.db.set_value('Item', item.name, 'image', attachments[0].file_url, update_modified=False)
        fixed += 1
    else:
        no_attach += 1

frappe.db.commit()
print(f'Fixed: {fixed}, No attachment: {no_attach}, Total: {len(items)}')
