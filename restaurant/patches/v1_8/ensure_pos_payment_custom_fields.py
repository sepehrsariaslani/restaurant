import frappe


CUSTOM_FIELDS = {
    "Restaurant Web Settings": [
        {
            "fieldname": "restaurant_pos_payment_section",
            "label": "POS Payment Integration",
            "fieldtype": "Section Break",
            "insert_after": "primary_cta_label",
        },
        {
            "fieldname": "restaurant_pos_payment_enabled",
            "label": "Enable POS Payment Integration",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_pos_payment_section",
        },
        {
            "fieldname": "restaurant_pos_payment_provider",
            "label": "POS Payment Provider",
            "fieldtype": "Select",
            "options": "manual\nwebhook",
            "default": "manual",
            "insert_after": "restaurant_pos_payment_enabled",
        },
        {
            "fieldname": "restaurant_pos_default_payment_method",
            "label": "Default POS Payment Method",
            "fieldtype": "Select",
            "options": "cash\ncard",
            "default": "cash",
            "insert_after": "restaurant_pos_payment_provider",
        },
        {
            "fieldname": "restaurant_pos_terminal_id",
            "label": "POS Terminal ID",
            "fieldtype": "Data",
            "insert_after": "restaurant_pos_default_payment_method",
        },
        {
            "fieldname": "restaurant_pos_webhook_url",
            "label": "POS Webhook URL",
            "fieldtype": "Data",
            "insert_after": "restaurant_pos_terminal_id",
        },
        {
            "fieldname": "restaurant_pos_webhook_api_key",
            "label": "POS Webhook API Key",
            "fieldtype": "Password",
            "insert_after": "restaurant_pos_webhook_url",
        },
        {
            "fieldname": "restaurant_pos_webhook_timeout_seconds",
            "label": "POS Webhook Timeout (seconds)",
            "fieldtype": "Int",
            "default": "20",
            "insert_after": "restaurant_pos_webhook_api_key",
        },
        {
            "fieldname": "restaurant_pos_webhook_success_values",
            "label": "POS Success Status Values",
            "fieldtype": "Data",
            "default": "success,paid,approved,ok,done",
            "insert_after": "restaurant_pos_webhook_timeout_seconds",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "restaurant_payment_method",
            "label": "Restaurant Payment Method",
            "fieldtype": "Select",
            "options": "cash\ncard",
            "default": "cash",
            "insert_after": "restaurant_include_service_items",
        },
        {
            "fieldname": "restaurant_payment_provider",
            "label": "Restaurant Payment Provider",
            "fieldtype": "Data",
            "insert_after": "restaurant_payment_method",
        },
        {
            "fieldname": "restaurant_payment_status",
            "label": "Restaurant Payment Status",
            "fieldtype": "Select",
            "options": "pending\npaid\nfailed\ncancelled",
            "default": "pending",
            "insert_after": "restaurant_payment_provider",
        },
        {
            "fieldname": "restaurant_payment_reference",
            "label": "Restaurant Payment Reference",
            "fieldtype": "Data",
            "insert_after": "restaurant_payment_status",
        },
        {
            "fieldname": "restaurant_payment_rrn",
            "label": "Restaurant Payment RRN",
            "fieldtype": "Data",
            "insert_after": "restaurant_payment_reference",
        },
        {
            "fieldname": "restaurant_payment_payload_json",
            "label": "Restaurant Payment Payload JSON",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_payment_rrn",
        },
    ],
}


def _ensure_custom_field(dt: str, field_def: dict):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {"doctype": "Custom Field", "dt": dt, **field_def}

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
