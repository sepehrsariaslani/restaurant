import frappe

@frappe.whitelist(allow_guest=True)
def test_tags_api():
    """Test tag parsing and item tags - guest accessible"""
    try:
        from restaurant.restaurant.api import _split_tags, get_item_detail
        
        # Test 1: _split_tags
        tags = _split_tags('رژیمی, پرفروش, وگان')
        
        # Test 2: get_item_detail for tagged item
        detail = get_item_detail('کاسه نودل میگو')
        
        return {
            'success': True,
            'split_tags_test': tags,
            'item_title': detail.get('title'),
            'item_tags': detail.get('tags'),
            'item_category': detail.get('category_title'),
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
