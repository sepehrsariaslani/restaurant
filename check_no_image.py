import frappe

items = frappe.get_all('Item', filters={'image': ['is', 'not set'], 'disabled': 0, 'restaurant_enabled': 1}, fields=['name','item_name'])
for i in items:
    print(f'{i.name}: {i.item_name}')
