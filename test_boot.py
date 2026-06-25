import frappe
frappe.init(site='veederakht.ir')
frappe.connect()
from restaurant.restaurant.api import get_menu_boot
boot = get_menu_boot()
cats = boot.get('categories', [])
featured = boot.get('featured_items', [])
print('categories:', len(cats))
print('featured:', len(featured))
for cat in cats[:3]:
    print('  cat:', cat.get('title'), '| show_on_homepage:', cat.get('show_on_homepage'))
for item in featured[:3]:
    print('  item:', item.get('title'), '| tags:', item.get('tags'))
frappe.destroy()
