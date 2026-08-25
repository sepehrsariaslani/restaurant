import frappe

def test_tags_field():
    # Ensure field exists
    from restaurant.api import _ensure_item_tags_field
    _ensure_item_tags_field()
    
    # Check if field exists
    has_field = frappe.db.has_column('Item', 'restaurant_item_tags')
    print(f'restaurant_item_tags field exists: {has_field}')
    
    # Get a sample item
    items = frappe.get_all('Item', fields=['name', 'item_name', 'restaurant_item_tags'], limit=3)
    for item in items:
        print(f"Item: {item.item_name}, Tags: {item.restaurant_item_tags}")
    
    # Test get_item_detail
    try:
        result = frappe.call('restaurant.api.get_item_detail', item_slug='test-nonexistent')
    except frappe.DoesNotExistError:
        print("get_item_detail works correctly - item not found as expected")
    except Exception as e:
        print(f"get_item_detail error: {e}")
        import traceback
        traceback.print_exc()

test_tags_field()
