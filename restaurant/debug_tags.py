import frappe
import json

@frappe.whitelist(allow_guest=True)
def debug_tags():
    """Debug tags - guest accessible"""
    result = {}
    
    # Check categories
    cats = frappe.get_all('Item Group', filters={'restaurant_is_menu_category': 1}, fields=['name', 'item_group_name', 'show_on_homepage', 'restaurant_slug'], limit=10)
    result['total_categories'] = len(cats)
    result['categories'] = [{'name': c.name, 'title': c.item_group_name, 'show_on_homepage': c.show_on_homepage, 'slug': c.restaurant_slug} for c in cats]
    
    # Check items with tags
    tagged = frappe.get_all('Item', filters={'disabled': 0, 'restaurant_enabled': 1, 'restaurant_item_tags': ['!=', '']}, fields=['name', 'item_name', 'restaurant_item_tags'], limit=10)
    result['tagged_items'] = [{'name': i.name, 'title': i.item_name, 'tags': i.restaurant_item_tags} for i in tagged]
    result['total_tagged'] = len(tagged)
    
    return result
