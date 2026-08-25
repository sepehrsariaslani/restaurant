import frappe
from frappe.utils import cint

def execute():
    # Add restaurant_slug to Item Group
    if not frappe.db.exists('Custom Field', 'Item Group-restaurant_slug'):
        cf = frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Item Group',
            'fieldname': 'restaurant_slug',
            'fieldtype': 'Data',
            'label': 'Restaurant Slug',
            'insert_after': 'image',
            'module': 'Restaurant',
        })
        cf.insert(ignore_permissions=True)
        frappe.db.commit()
        print('Added restaurant_slug to Item Group')
    else:
        print('restaurant_slug already exists on Item Group')

    # Add restaurant_sort_order to Item Group
    if not frappe.db.exists('Custom Field', 'Item Group-restaurant_sort_order'):
        cf2 = frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Item Group',
            'fieldname': 'restaurant_sort_order',
            'fieldtype': 'Int',
            'label': 'Restaurant Sort Order',
            'insert_after': 'restaurant_slug',
            'module': 'Restaurant',
        })
        cf2.insert(ignore_permissions=True)
        frappe.db.commit()
        print('Added restaurant_sort_order to Item Group')
    else:
        print('restaurant_sort_order already exists on Item Group')

    # Also check Item Group for restaurant_is_menu_category
    if not frappe.db.exists('Custom Field', 'Item Group-restaurant_is_menu_category'):
        cf3 = frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Item Group',
            'fieldname': 'restaurant_is_menu_category',
            'fieldtype': 'Check',
            'label': 'Is Menu Category',
            'insert_after': 'restaurant_sort_order',
            'module': 'Restaurant',
            'default': '0',
        })
        cf3.insert(ignore_permissions=True)
        frappe.db.commit()
        print('Added restaurant_is_menu_category to Item Group')
    else:
        print('restaurant_is_menu_category already exists on Item Group')

    # Check for show_on_homepage
    if not frappe.db.exists('Custom Field', 'Item Group-show_on_homepage'):
        cf4 = frappe.get_doc({
            'doctype': 'Custom Field',
            'dt': 'Item Group',
            'fieldname': 'show_on_homepage',
            'fieldtype': 'Check',
            'label': 'Show on Homepage',
            'insert_after': 'restaurant_is_menu_category',
            'module': 'Restaurant',
            'default': '0',
        })
        cf4.insert(ignore_permissions=True)
        frappe.db.commit()
        print('Added show_on_homepage to Item Group')
    else:
        print('show_on_homepage already exists on Item Group')

    print('Done adding custom fields')
