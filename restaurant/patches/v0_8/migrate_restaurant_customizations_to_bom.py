import json

import frappe
from frappe.utils import cint, flt


BOM_CUSTOM_FIELDS = {
    "BOM": [
        {
            "fieldname": "restaurant_modifier_groups_json",
            "label": "Restaurant Modifier Groups JSON",
            "fieldtype": "Long Text",
            "insert_after": "description",
        },
        {
            "fieldname": "restaurant_menu_item_ref",
            "label": "Restaurant Menu Item Ref",
            "fieldtype": "Link",
            "options": "Item",
            "insert_after": "restaurant_modifier_groups_json",
        },
    ],
    "BOM Item": [
        {
            "fieldname": "restaurant_customer_label",
            "label": "Restaurant Customer Label",
            "fieldtype": "Data",
            "insert_after": "description",
        },
        {
            "fieldname": "restaurant_is_included_by_default",
            "label": "Restaurant Is Included By Default",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_customer_label",
        },
        {
            "fieldname": "restaurant_can_remove",
            "label": "Restaurant Can Remove",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_is_included_by_default",
        },
        {
            "fieldname": "restaurant_is_required",
            "label": "Restaurant Is Required",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_can_remove",
        },
        {
            "fieldname": "restaurant_is_editable_qty",
            "label": "Restaurant Is Editable Qty",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_is_required",
        },
        {
            "fieldname": "restaurant_min_multiplier",
            "label": "Restaurant Min Multiplier",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_is_editable_qty",
        },
        {
            "fieldname": "restaurant_max_multiplier",
            "label": "Restaurant Max Multiplier",
            "fieldtype": "Float",
            "default": "3",
            "insert_after": "restaurant_min_multiplier",
        },
        {
            "fieldname": "restaurant_step_multiplier",
            "label": "Restaurant Step Multiplier",
            "fieldtype": "Float",
            "default": "0.5",
            "insert_after": "restaurant_max_multiplier",
        },
        {
            "fieldname": "restaurant_extra_when_added",
            "label": "Restaurant Extra When Added",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_step_multiplier",
        },
    ],
    "Item Alternative": [
        {
            "fieldname": "restaurant_modifier_group",
            "label": "Restaurant Modifier Group",
            "fieldtype": "Data",
            "insert_after": "alternative_item_name",
        },
        {
            "fieldname": "restaurant_modifier_group_title",
            "label": "Restaurant Modifier Group Title",
            "fieldtype": "Data",
            "insert_after": "restaurant_modifier_group",
        },
        {
            "fieldname": "restaurant_selection_mode",
            "label": "Restaurant Selection Mode",
            "fieldtype": "Select",
            "options": "single\nmulti",
            "insert_after": "restaurant_modifier_group_title",
        },
        {
            "fieldname": "restaurant_required",
            "label": "Restaurant Required",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_selection_mode",
        },
        {
            "fieldname": "restaurant_min_select",
            "label": "Restaurant Min Select",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "restaurant_required",
        },
        {
            "fieldname": "restaurant_max_select",
            "label": "Restaurant Max Select",
            "fieldtype": "Int",
            "default": "1",
            "insert_after": "restaurant_min_select",
        },
        {
            "fieldname": "restaurant_price_delta",
            "label": "Restaurant Price Delta",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_max_select",
        },
        {
            "fieldname": "restaurant_recipe_multiplier",
            "label": "Restaurant Recipe Multiplier",
            "fieldtype": "Float",
            "default": "1",
            "insert_after": "restaurant_price_delta",
        },
        {
            "fieldname": "restaurant_is_default_modifier",
            "label": "Restaurant Is Default Modifier",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_recipe_multiplier",
        },
        {
            "fieldname": "restaurant_is_modifier_option",
            "label": "Restaurant Is Modifier Option",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_is_default_modifier",
        },
    ],
}


def _ensure_custom_field(dt: str, field_def: dict):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {
        "doctype": "Custom Field",
        "dt": dt,
        **field_def,
        "module": "Restaurant",
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


def _ensure_bom_for_item(item_doc):
    bom_name = (item_doc.get("restaurant_bom_template") or "").strip()
    if bom_name and frappe.db.exists("BOM", bom_name):
        return frappe.get_doc("BOM", bom_name)

    default_bom = (item_doc.get("default_bom") or "").strip()
    if default_bom and frappe.db.exists("BOM", default_bom):
        return frappe.get_doc("BOM", default_bom)

    bom_name = frappe.db.get_value(
        "BOM",
        {
            "item": item_doc.item_code,
            "is_default": 1,
            "is_active": 1,
            "docstatus": 1,
        },
        "name",
    )
    if bom_name:
        return frappe.get_doc("BOM", bom_name)

    company = frappe.db.get_value("Company", {}, "name")
    if not company:
        return None

    currency = frappe.db.get_value("Company", company, "default_currency")
    bom = frappe.get_doc(
        {
            "doctype": "BOM",
            "item": item_doc.item_code,
            "company": company,
            "currency": currency,
            "conversion_rate": 1,
            "quantity": flt(item_doc.get("restaurant_recipe_yield_qty") or 1) or 1,
            "uom": item_doc.stock_uom,
            "is_default": 1,
            "is_active": 1,
            "items": [],
        }
    )
    bom.insert(ignore_permissions=True)
    bom.submit()
    return frappe.get_doc("BOM", bom.name)


def _modifier_groups_payload(item_doc):
    bom_name = (item_doc.get("restaurant_bom_template") or item_doc.get("default_bom") or "").strip()
    if bom_name and frappe.db.exists("BOM", bom_name):
        bom_doc = frappe.get_doc("BOM", bom_name)
        rows = frappe.get_all(
            "Item Alternative",
            filters={
                "item_code": item_doc.item_code,
                "restaurant_is_modifier_option": 1,
            },
            fields=[
                "alternative_item_code",
                "restaurant_modifier_group",
                "restaurant_modifier_group_title",
                "restaurant_selection_mode",
                "restaurant_required",
                "restaurant_min_select",
                "restaurant_max_select",
                "restaurant_price_delta",
                "restaurant_recipe_multiplier",
                "restaurant_is_default_modifier",
            ],
            ignore_permissions=True,
        )
        if rows:
            grouped = {}
            for row in rows:
                group_name = row.get("restaurant_modifier_group") or row.get("restaurant_modifier_group_title")
                if not group_name:
                    continue
                payload = grouped.setdefault(
                    group_name,
                    {
                        "group_name": group_name,
                        "title": row.get("restaurant_modifier_group_title") or group_name,
                        "selection_mode": row.get("restaurant_selection_mode") or "single",
                        "required": cint(row.get("restaurant_required")),
                        "min_select": cint(row.get("restaurant_min_select")),
                        "max_select": max(cint(row.get("restaurant_max_select") or 1), 1),
                        "options": [],
                    },
                )
                payload["options"].append(
                    {
                        "name": row.get("alternative_item_code"),
                        "price_delta": flt(row.get("restaurant_price_delta")),
                        "recipe_multiplier": flt(row.get("restaurant_recipe_multiplier") or 1),
                        "is_default": cint(row.get("restaurant_is_default_modifier")),
                    }
                )
            return list(grouped.values())

        return frappe.parse_json(bom_doc.get("restaurant_modifier_groups_json") or "[]") or []

    return []


def _ensure_item_alternative(base_item_code, alternative_item_code, group_payload, option_payload):
    if not base_item_code or not alternative_item_code or base_item_code == alternative_item_code:
        return

    name = frappe.db.get_value(
        "Item Alternative",
        {"item_code": base_item_code, "alternative_item_code": alternative_item_code},
        "name",
    )
    payload = {
        "doctype": "Item Alternative",
        "item_code": base_item_code,
        "alternative_item_code": alternative_item_code,
        "restaurant_modifier_group": group_payload.get("group_name"),
        "restaurant_modifier_group_title": group_payload.get("title"),
        "restaurant_selection_mode": group_payload.get("selection_mode") or "single",
        "restaurant_required": cint(group_payload.get("required")),
        "restaurant_min_select": cint(group_payload.get("min_select")),
        "restaurant_max_select": cint(group_payload.get("max_select") or 1),
        "restaurant_price_delta": flt(option_payload.get("price_delta")),
        "restaurant_recipe_multiplier": flt(option_payload.get("recipe_multiplier") or 1),
        "restaurant_is_default_modifier": cint(option_payload.get("is_default")),
        "restaurant_is_modifier_option": 1,
    }

    if name:
        doc = frappe.get_doc("Item Alternative", name)
        changed = False
        for key, value in payload.items():
            if key == "doctype":
                continue
            if doc.get(key) != value:
                doc.set(key, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return

    frappe.get_doc(payload).insert(ignore_permissions=True)


def _sync_item_to_bom(item_name):
    item_doc = frappe.get_doc("Item", item_name)
    bom = _ensure_bom_for_item(item_doc)
    if not bom:
        return

    ingredient_rows = sorted(item_doc.get("restaurant_ingredients") or [], key=lambda d: cint(d.sort_order or 0))
    bom.set("items", [])
    for row in ingredient_rows:
        ingredient_item = (row.get("ingredient_item") or "").strip()
        ingredient_name = (row.get("ingredient_name") or ingredient_item or "Ingredient").strip()
        if not ingredient_item or not frappe.db.exists("Item", ingredient_item):
            continue

        qty = flt(row.get("base_qty") or 0)
        if qty <= 0:
            qty = 1 if cint(row.get("is_included_by_default")) else 0.5

        bom.append(
            "items",
            {
                "item_code": ingredient_item,
                "item_name": ingredient_name,
                "qty": qty,
                "uom": row.get("qty_uom") or frappe.db.get_value("Item", ingredient_item, "stock_uom") or item_doc.stock_uom,
                "allow_alternative_item": 1 if cint(row.get("is_editable_qty")) or cint(row.get("can_remove")) else 0,
                "description": ingredient_name,
                "restaurant_customer_label": row.get("customer_label") or ingredient_name,
                "restaurant_is_included_by_default": cint(row.get("is_included_by_default")),
                "restaurant_can_remove": cint(row.get("can_remove")),
                "restaurant_is_required": cint(row.get("is_required")),
                "restaurant_is_editable_qty": cint(row.get("is_editable_qty")) if row.get("is_editable_qty") is not None else 1,
                "restaurant_min_multiplier": flt(row.get("min_multiplier")),
                "restaurant_max_multiplier": flt(row.get("max_multiplier") or 3),
                "restaurant_step_multiplier": flt(row.get("step_multiplier") or 0.5),
                "restaurant_extra_when_added": flt(row.get("extra_when_added")),
            },
        )

    modifier_groups = _modifier_groups_payload(item_doc)
    bom.restaurant_modifier_groups_json = json.dumps(modifier_groups, ensure_ascii=False)
    bom.restaurant_menu_item_ref = item_doc.name
    bom.quantity = flt(item_doc.get("restaurant_recipe_yield_qty") or bom.quantity or 1) or 1
    bom.uom = item_doc.get("restaurant_recipe_uom") or item_doc.stock_uom
    bom.is_default = 1
    bom.is_active = 1
    bom.flags.ignore_validate_update_after_submit = True
    bom.save(ignore_permissions=True)
    if bom.docstatus == 0:
        bom.submit()

    for group in modifier_groups:
        for option in group.get("options") or []:
            alt_item_code = (option.get("name") or "").strip()
            if alt_item_code and frappe.db.exists("Item", alt_item_code):
                _ensure_item_alternative(item_doc.item_code, alt_item_code, group, option)

    if frappe.db.has_column("Item", "restaurant_bom_template") and item_doc.get("restaurant_bom_template") != bom.name:
        item_doc.db_set("restaurant_bom_template", bom.name, update_modified=False)
    if frappe.db.has_column("Item", "default_bom") and item_doc.get("default_bom") != bom.name:
        item_doc.db_set("default_bom", bom.name, update_modified=False)
    if frappe.db.has_column("Item", "restaurant_requires_bom"):
        item_doc.db_set("restaurant_requires_bom", 1, update_modified=False)


def execute():
    for dt, field_defs in BOM_CUSTOM_FIELDS.items():
        for field_def in field_defs:
            _ensure_custom_field(dt, field_def)

    if not frappe.db.exists("DocType", "Item") or not frappe.db.has_column("Item", "restaurant_ingredients"):
        frappe.clear_cache()
        frappe.db.commit()
        return

    items = frappe.get_all("Item", filters={"restaurant_enabled": 1}, pluck="name", ignore_permissions=True)
    for item_name in items:
        try:
            _sync_item_to_bom(item_name)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Restaurant BOM migration failed for {item_name}")

    frappe.clear_cache()
    frappe.db.commit()
