import frappe


CUSTOM_FIELDS = {
    "Restaurant Web Settings": [
        {
            "fieldname": "snapp_amount_multiplier",
            "label": "Snapp Amount Multiplier",
            "fieldtype": "Float",
            "default": "10",
            "insert_after": "snapp_lookback_minutes",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "restaurant_external_delivery_type",
            "label": "Restaurant External Delivery Type",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_state",
        },
        {
            "fieldname": "restaurant_external_payment_method",
            "label": "Restaurant External Payment Method",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_delivery_type",
        },
        {
            "fieldname": "restaurant_external_factor_number",
            "label": "Restaurant External Factor Number",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_payment_method",
        },
        {
            "fieldname": "restaurant_external_discount",
            "label": "Restaurant External Discount",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_factor_number",
        },
        {
            "fieldname": "restaurant_external_delivery_cost",
            "label": "Restaurant External Delivery Cost",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_discount",
        },
        {
            "fieldname": "restaurant_external_packaging_cost",
            "label": "Restaurant External Packaging Cost",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_delivery_cost",
        },
        {
            "fieldname": "restaurant_external_tax",
            "label": "Restaurant External Tax",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_packaging_cost",
        },
        {
            "fieldname": "restaurant_external_service_cost",
            "label": "Restaurant External Service Cost",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_tax",
        },
        {
            "fieldname": "restaurant_external_service_fee",
            "label": "Restaurant External Service Fee",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_service_cost",
        },
        {
            "fieldname": "restaurant_external_tip",
            "label": "Restaurant External Tip",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_service_fee",
        },
        {
            "fieldname": "restaurant_external_refund_amount",
            "label": "Restaurant External Refund Amount",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_tip",
        },
        {
            "fieldname": "restaurant_external_final_price",
            "label": "Restaurant External Final Price",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_refund_amount",
        },
        {
            "fieldname": "restaurant_external_discount_amount",
            "label": "Restaurant External Discount Amount",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_final_price",
        },
        {
            "fieldname": "restaurant_external_discount_code",
            "label": "Restaurant External Discount Code",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_discount_amount",
        },
        {
            "fieldname": "restaurant_external_discount_type",
            "label": "Restaurant External Discount Type",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_discount_code",
        },
        {
            "fieldname": "restaurant_external_vendor_name",
            "label": "Restaurant External Vendor Name",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_discount_type",
        },
        {
            "fieldname": "restaurant_external_vendor_subdomain",
            "label": "Restaurant External Vendor Subdomain",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_vendor_name",
        },
    ],
    "Sales Order Item": [
        {
            "fieldname": "restaurant_external_discount",
            "label": "Restaurant External Discount",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_item_title",
        },
        {
            "fieldname": "restaurant_external_packaging_cost",
            "label": "Restaurant External Packaging Cost",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_external_discount",
        },
        {
            "fieldname": "restaurant_external_with_tax",
            "label": "Restaurant External With Tax",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_external_packaging_cost",
        },
        {
            "fieldname": "restaurant_external_toppings_json",
            "label": "Restaurant External Toppings JSON",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_external_with_tax",
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
