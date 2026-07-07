import frappe


def _ensure_custom_field(dt: str, field_def: dict):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {"doctype": "Custom Field", "dt": dt, "module": "Restaurant", **field_def}

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
    fields = [
        {
            "fieldname": "restaurant_auto_flow_section",
            "label": "اتوماسیون تولید رستوران",
            "fieldtype": "Section Break",
            "insert_after": "restaurant_pos_webhook_success_values",
        },
        {
            "fieldname": "restaurant_auto_flow_enabled",
            "label": "فعال‌سازی اتوماسیون کامل",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_section",
        },
        {
            "fieldname": "restaurant_auto_flow_on_order_submit",
            "label": "اجرا بعد از ثبت سفارش",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_enabled",
        },
        {
            "fieldname": "restaurant_auto_flow_on_payment",
            "label": "اجرا بعد از پرداخت",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_on_order_submit",
        },
        {
            "fieldname": "restaurant_auto_flow_submit_work_order",
            "label": "ثبت خودکار دستور تولید",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_on_payment",
        },
        {
            "fieldname": "restaurant_auto_flow_material_transfer",
            "label": "انتقال خودکار مواد اولیه",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_auto_flow_submit_work_order",
        },
        {
            "fieldname": "restaurant_auto_flow_manufacture",
            "label": "ثبت خودکار تولید",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_material_transfer",
        },
        {
            "fieldname": "restaurant_auto_flow_submit_stock_entries",
            "label": "ثبت نهایی خودکار اسناد انبار",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_manufacture",
        },
        {
            "fieldname": "restaurant_auto_flow_mark_ready",
            "label": "تغییر خودکار وضعیت به آماده",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_submit_stock_entries",
        },
        {
            "fieldname": "restaurant_auto_flow_mark_delivered_on_paid",
            "label": "تحویل خودکار بعد از پرداخت",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_mark_ready",
        },
        {
            "fieldname": "restaurant_auto_flow_create_delivery_note",
            "label": "ایجاد خودکار حواله تحویل",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_auto_flow_mark_delivered_on_paid",
        },
        {
            "fieldname": "restaurant_auto_flow_submit_delivery_note",
            "label": "ثبت نهایی خودکار حواله تحویل",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_auto_flow_create_delivery_note",
        },
    ]

    for field_def in fields:
        _ensure_custom_field("Restaurant Web Settings", field_def)

    frappe.clear_cache(doctype="Restaurant Web Settings")
    frappe.db.commit()
