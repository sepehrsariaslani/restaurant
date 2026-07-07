import frappe


CUSTOM_FIELDS = {
    "Restaurant Web Settings": [
        {
            "fieldname": "snapp_section_break",
            "label": "Snapp Sync Settings",
            "fieldtype": "Section Break",
            "insert_after": "primary_cta_label",
        },
        {
            "fieldname": "snapp_sync_enabled",
            "label": "Snapp Sync Enabled",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "snapp_section_break",
        },
        {
            "fieldname": "snapp_api_base_url",
            "label": "Snapp API Base URL",
            "fieldtype": "Data",
            "default": "https://api.prod.snapp-store.com",
            "insert_after": "snapp_sync_enabled",
        },
        {
            "fieldname": "snapp_origin_url",
            "label": "Snapp Origin URL",
            "fieldtype": "Data",
            "insert_after": "snapp_api_base_url",
        },
        {
            "fieldname": "snapp_hostdomain",
            "label": "Snapp Host Domain",
            "fieldtype": "Data",
            "insert_after": "snapp_origin_url",
        },
        {
            "fieldname": "snapp_bearer_token",
            "label": "Snapp Bearer Token",
            "fieldtype": "Password",
            "insert_after": "snapp_hostdomain",
        },
        {
            "fieldname": "snapp_page_size",
            "label": "Snapp Page Size",
            "fieldtype": "Int",
            "default": "50",
            "insert_after": "snapp_bearer_token",
        },
        {
            "fieldname": "snapp_lookback_minutes",
            "label": "Snapp Lookback Minutes",
            "fieldtype": "Int",
            "default": "180",
            "insert_after": "snapp_page_size",
        },
        {
            "fieldname": "snapp_write_debug_json",
            "label": "Snapp Write Debug JSON",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "snapp_lookback_minutes",
        },
        {
            "fieldname": "snapp_last_success_at",
            "label": "Snapp Last Success At",
            "fieldtype": "Datetime",
            "read_only": 1,
            "insert_after": "snapp_write_debug_json",
        },
        {
            "fieldname": "snapp_last_error_at",
            "label": "Snapp Last Error At",
            "fieldtype": "Datetime",
            "read_only": 1,
            "insert_after": "snapp_last_success_at",
        },
        {
            "fieldname": "snapp_last_error_message",
            "label": "Snapp Last Error Message",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "snapp_last_error_at",
        },
        {
            "fieldname": "snapp_last_seen_created_at",
            "label": "Snapp Last Seen Created At",
            "fieldtype": "Datetime",
            "read_only": 1,
            "insert_after": "snapp_last_error_message",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "restaurant_external_source",
            "label": "Restaurant External Source",
            "fieldtype": "Data",
            "insert_after": "restaurant_payload_json",
        },
        {
            "fieldname": "restaurant_external_order_id",
            "label": "Restaurant External Order ID",
            "fieldtype": "Data",
            "unique": 1,
            "insert_after": "restaurant_external_source",
        },
        {
            "fieldname": "restaurant_external_bill_number",
            "label": "Restaurant External Bill Number",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_order_id",
        },
        {
            "fieldname": "restaurant_external_state",
            "label": "Restaurant External State",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_bill_number",
        },
        {
            "fieldname": "restaurant_external_payload_json",
            "label": "Restaurant External Payload JSON",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_external_state",
        },
    ],
    "Sales Order Item": [
        {
            "fieldname": "restaurant_external_line_id",
            "label": "Restaurant External Line ID",
            "fieldtype": "Data",
            "insert_after": "description",
        },
        {
            "fieldname": "restaurant_external_menu_item_id",
            "label": "Restaurant External Menu Item ID",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_line_id",
        },
        {
            "fieldname": "restaurant_external_item_title",
            "label": "Restaurant External Item Title",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_menu_item_id",
        },
    ],
    "Item": [
        {
            "fieldname": "restaurant_external_menu_item_id",
            "label": "Restaurant External Menu Item ID",
            "fieldtype": "Data",
            "search_index": 1,
            "insert_after": "restaurant_branch",
        },
    ],
}


def _ensure_custom_field(dt, field_def):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {
        "doctype": "Custom Field",
        "dt": dt,
        **field_def,
    }

    if existing_name:
        doc = frappe.get_doc("Custom Field", existing_name)
        changed = False
        for key, value in payload.items():
            if key == "doctype":
                continue
            if doc.get(key) != value:
                doc.set(key, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True)
    return doc.name


def execute():
    for dt, field_defs in CUSTOM_FIELDS.items():
        for field_def in field_defs:
            _ensure_custom_field(dt, field_def)

    frappe.clear_cache()
    frappe.db.commit()
