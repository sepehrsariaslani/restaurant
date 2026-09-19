import frappe


CUSTOM_FIELDS = {
    "Restaurant Web Settings": [
        {
            "fieldname": "snappfood_section_break",
            "label": "اتصال Food Partner",
            "fieldtype": "Section Break",
            "insert_after": "snapp_section_break",
        },
        {
            "fieldname": "snapp_vendor_id",
            "label": "شناسه فروشنده Food Partner",
            "fieldtype": "Data",
            "insert_after": "snappfood_section_break",
        },
        {
            "fieldname": "snapp_report_url",
            "label": "آدرس گزارش سفارش Food Partner",
            "fieldtype": "Data",
            "default": "https://snappfood.ir/vms/v3/restaurant/report",
            "insert_after": "snapp_vendor_id",
        },
        {
            "fieldname": "snapp_menu_api_base_url",
            "label": "آدرس API منوی Food Partner",
            "fieldtype": "Data",
            "default": "https://apigw.snappfood.ir",
            "insert_after": "snapp_report_url",
        },
        {
            "fieldname": "snapp_auto_sync_invoices",
            "label": "ساخت خودکار فاکتور فروش",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "snapp_menu_api_base_url",
        },
        {
            "fieldname": "snapp_require_item_mapping",
            "label": "جلوگیری از سفارش کالای نگاشت‌نشده",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "snapp_auto_sync_invoices",
        },
        {
            "fieldname": "snapp_default_customer",
            "label": "مشتری پیش‌فرض Food Partner",
            "fieldtype": "Link",
            "options": "Customer",
            "insert_after": "snapp_require_item_mapping",
        },
        {
            "fieldname": "snapp_last_menu_sync_at",
            "label": "آخرین دریافت منو",
            "fieldtype": "Datetime",
            "read_only": 1,
            "insert_after": "snapp_default_customer",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "restaurant_external_customer_id",
            "label": "شناسه مشتری خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_factor_number",
        },
        {
            "fieldname": "restaurant_external_order_created_at",
            "label": "زمان ایجاد سفارش خارجی",
            "fieldtype": "Datetime",
            "insert_after": "restaurant_external_customer_id",
        },
    ],
    "Sales Invoice": [
        {
            "fieldname": "restaurant_external_source",
            "label": "منبع خارجی سفارش",
            "fieldtype": "Data",
            "insert_after": "remarks",
        },
        {
            "fieldname": "restaurant_external_order_id",
            "label": "شناسه سفارش Food Partner",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_source",
        },
        {
            "fieldname": "restaurant_external_bill_number",
            "label": "شماره فاکتور خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_order_id",
        },
        {
            "fieldname": "restaurant_external_state",
            "label": "وضعیت خارجی سفارش",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_bill_number",
        },
        {
            "fieldname": "restaurant_external_payment_method",
            "label": "روش پرداخت خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_state",
        },
        {
            "fieldname": "restaurant_external_payload_json",
            "label": "داده خام سفارش خارجی",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_external_payment_method",
        },
    ],
    "Sales Invoice Item": [
        {
            "fieldname": "restaurant_external_line_id",
            "label": "شناسه ردیف خارجی",
            "fieldtype": "Data",
            "insert_after": "description",
        },
        {
            "fieldname": "restaurant_external_menu_item_id",
            "label": "شناسه آیتم منوی خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_line_id",
        },
        {
            "fieldname": "restaurant_external_item_title",
            "label": "عنوان آیتم خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_menu_item_id",
        },
    ],
    "Sales Order Item": [
        {
            "fieldname": "restaurant_external_product_id",
            "label": "شناسه محصول خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_menu_item_id",
        },
        {
            "fieldname": "restaurant_external_variation_id",
            "label": "شناسه variation خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_product_id",
        },
    ],
    "Customer": [
        {
            "fieldname": "restaurant_external_source",
            "label": "منبع مشتری خارجی",
            "fieldtype": "Data",
            "insert_after": "customer_group",
        },
        {
            "fieldname": "restaurant_external_customer_id",
            "label": "شناسه مشتری Food Partner",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_source",
        },
    ],
    "Item": [
        {
            "fieldname": "restaurant_external_product_id",
            "label": "شناسه محصول Food Partner",
            "fieldtype": "Data",
            "search_index": 1,
            "insert_after": "restaurant_external_menu_item_id",
        },
        {
            "fieldname": "restaurant_external_variation_id",
            "label": "شناسه Variation Food Partner",
            "fieldtype": "Data",
            "search_index": 1,
            "insert_after": "restaurant_external_product_id",
        },
        {
            "fieldname": "restaurant_external_product_hash_id",
            "label": "Product Hash ID خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_variation_id",
        },
        {
            "fieldname": "restaurant_external_variation_hash_id",
            "label": "Variation Hash ID خارجی",
            "fieldtype": "Data",
            "insert_after": "restaurant_external_product_hash_id",
        },
        {
            "fieldname": "restaurant_external_mapping_status",
            "label": "وضعیت نگاشت Food Partner",
            "fieldtype": "Select",
            "options": "\nUnmapped\nSuggested\nMapped",
            "default": "Unmapped",
            "insert_after": "restaurant_external_variation_hash_id",
        },
    ],
}


def _ensure_custom_field(dt, field_def):
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
    return frappe.get_doc(payload).insert(ignore_permissions=True).name


def execute():
    for doctype, fields in CUSTOM_FIELDS.items():
        for field_def in fields:
            _ensure_custom_field(doctype, field_def)
    frappe.clear_cache()
    frappe.db.commit()
