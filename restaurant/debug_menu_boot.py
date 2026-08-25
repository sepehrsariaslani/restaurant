import frappe
import json

@frappe.whitelist(allow_guest=True)
def debug_menu_boot():
    """Debug menu boot output"""
    try:
        from restaurant.restaurant.api import _get_core_menu_boot, _core_category_filters, _has_column
        
        # Check categories
        cat_filters = _core_category_filters(is_subcategory=0)
        categories = frappe.get_all(
            "Item Group",
            filters=cat_filters,
            fields=["name", "item_group_name", "restaurant_slug", "show_on_homepage"],
            limit_page_length=5000,
        )
        
        # Filter by show_on_homepage
        if _has_column("Item Group", "show_on_homepage"):
            filtered = [c for c in categories if c.get("show_on_homepage") != 0]
        else:
            filtered = categories
        
        return {
            "success": True,
            "total_categories": len(categories),
            "filtered_categories": len(filtered),
            "sample": [{"name": c.name, "title": c.item_group_name, "show_on_homepage": c.show_on_homepage} for c in categories[:5]],
        }
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": frappe.get_traceback()}
