import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

existing = frappe.db.get_value('Custom Field', {'dt': 'Item', 'fieldname': 'restaurant_coming_soon'}, 'name')
if existing:
    print(f'EXISTS:{existing}')
else:
    try:
        doc = create_custom_field('Item', frappe._dict({
            'fieldname': 'restaurant_coming_soon',
            'label': 'به‌زودی',
            'fieldtype': 'Check',
            'insert_after': 'restaurant_item_tag_table',
            'default': 0,
            'description': 'اگر فعال باشد به جای قیمت نوشته به‌زودی نمایش داده می‌شود'
        }))
        frappe.db.commit()
        print(f'CREATED:{doc}')
    except Exception as e:
        print(f'ERROR:{e}')
