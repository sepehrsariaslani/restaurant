import json

import frappe
from frappe.utils import cint, flt


LEGACY_ITEM_FIELDS = ["restaurant_ingredients", "restaurant_modifier_groups"]


def _get_or_create_bom(item_doc):
    for bom_name in [item_doc.get("restaurant_bom_template"), item_doc.get("default_bom")]:
        bom_name = (bom_name or "").strip()
        if bom_name and frappe.db.exists("BOM", bom_name):
            return frappe.get_doc("BOM", bom_name)

    bom_name = frappe.db.get_value(
        "BOM",
        {"item": item_doc.item_code, "is_default": 1, "is_active": 1, "docstatus": 1},
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


def _migrate_legacy_ingredients_to_bom(item_doc, bom_doc):
    if not frappe.db.has_column("Item", "restaurant_ingredients"):
        return False

    legacy_rows = sorted(item_doc.get("restaurant_ingredients") or [], key=lambda d: cint(d.sort_order or 0))
    if not legacy_rows:
        return False

    changed = False
    existing = {row.item_code: row for row in (bom_doc.get("items") or []) if row.get("item_code")}

    for row in legacy_rows:
        item_code = (row.get("ingredient_item") or "").strip()
        if not item_code or not frappe.db.exists("Item", item_code):
            continue

        qty = flt(row.get("base_qty") or 0)
        if qty <= 0:
            qty = 1 if cint(row.get("is_included_by_default")) else 0.5

        target = existing.get(item_code)
        payload = {
            "item_code": item_code,
            "item_name": row.get("ingredient_name") or frappe.db.get_value("Item", item_code, "item_name"),
            "qty": qty,
            "uom": row.get("qty_uom") or frappe.db.get_value("Item", item_code, "stock_uom") or item_doc.stock_uom,
            "allow_alternative_item": 1 if cint(row.get("is_editable_qty")) or cint(row.get("can_remove")) else 0,
            "description": row.get("ingredient_name") or frappe.db.get_value("Item", item_code, "item_name"),
            "restaurant_customer_label": row.get("customer_label") or row.get("ingredient_name") or frappe.db.get_value("Item", item_code, "item_name"),
            "restaurant_is_included_by_default": cint(row.get("is_included_by_default")),
            "restaurant_can_remove": cint(row.get("can_remove")),
            "restaurant_is_required": cint(row.get("is_required")),
            "restaurant_is_editable_qty": cint(row.get("is_editable_qty")) if row.get("is_editable_qty") is not None else 1,
            "restaurant_min_multiplier": flt(row.get("min_multiplier")),
            "restaurant_max_multiplier": flt(row.get("max_multiplier") or 3),
            "restaurant_step_multiplier": flt(row.get("step_multiplier") or 0.5),
            "restaurant_extra_when_added": flt(row.get("extra_when_added")),
        }

        if target:
            row_changed = False
            for key, value in payload.items():
                if target.get(key) != value:
                    target.set(key, value)
                    row_changed = True
            changed = changed or row_changed
        else:
            bom_doc.append("items", payload)
            changed = True

    return changed


def _legacy_modifier_groups(item_doc):
    if not frappe.db.has_column("Item", "restaurant_modifier_groups"):
        return []
    if not frappe.db.exists("DocType", "Restaurant Modifier Group"):
        return []

    rows = []
    for link in sorted(item_doc.get("restaurant_modifier_groups") or [], key=lambda d: cint(d.sort_order or 0)):
        group_name = link.get("modifier_group")
        if not group_name or not frappe.db.exists("Restaurant Modifier Group", group_name):
            continue

        group_doc = frappe.get_doc("Restaurant Modifier Group", group_name)
        if not cint(group_doc.get("is_active")):
            continue

        options = []
        for option in sorted(group_doc.get("options") or [], key=lambda d: cint(d.sort_order or 0)):
            options.append(
                {
                    "name": option.get("option_name"),
                    "price_delta": flt(option.get("price_delta")),
                    "recipe_multiplier": flt(option.get("recipe_multiplier") or 1),
                    "is_default": cint(option.get("is_default")),
                }
            )

        selection_mode = group_doc.get("selection_mode") or "single"
        required = cint(link.get("required") if link.get("required") is not None else group_doc.get("required"))
        min_select = cint(link.get("min_select") if link.get("min_select") is not None else group_doc.get("min_select"))
        max_select = cint(link.get("max_select") if link.get("max_select") is not None else group_doc.get("max_select") or 1)
        if selection_mode == "single":
            min_select = 1 if required else 0
            max_select = 1
        else:
            min_select = max(min_select, 0)
            max_select = max(max_select, 1)

        rows.append(
            {
                "group_name": group_doc.name,
                "title": group_doc.get("title"),
                "selection_mode": selection_mode,
                "required": required,
                "min_select": min_select,
                "max_select": max_select,
                "options": options,
            }
        )

    return rows


def _migrate_legacy_modifiers(item_doc, bom_doc):
    groups = _legacy_modifier_groups(item_doc)
    if not groups:
        return False

    changed = False
    existing_json = (bom_doc.get("restaurant_modifier_groups_json") or "").strip()
    if not existing_json:
        bom_doc.restaurant_modifier_groups_json = json.dumps(groups, ensure_ascii=False)
        changed = True

    for group in groups:
        for option in group.get("options") or []:
            alt_item_code = (option.get("name") or "").strip()
            if alt_item_code and frappe.db.exists("Item", alt_item_code):
                _ensure_item_alternative(item_doc.item_code, alt_item_code, group, option)

    return changed


def _remove_legacy_custom_fields():
    for fieldname in LEGACY_ITEM_FIELDS:
        custom_field_name = frappe.db.get_value("Custom Field", {"dt": "Item", "fieldname": fieldname}, "name")
        if not custom_field_name:
            continue
        try:
            frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to delete Custom Field: {custom_field_name}")


def execute():
    if frappe.db.exists("DocType", "Item"):
        item_names = frappe.get_all(
            "Item",
            filters={"restaurant_enabled": 1},
            pluck="name",
            ignore_permissions=True,
        )
        for item_name in item_names:
            try:
                item_doc = frappe.get_doc("Item", item_name)
                bom_doc = _get_or_create_bom(item_doc)
                if not bom_doc:
                    continue

                changed = _migrate_legacy_ingredients_to_bom(item_doc, bom_doc)
                changed = _migrate_legacy_modifiers(item_doc, bom_doc) or changed

                if changed:
                    bom_doc.is_default = 1
                    bom_doc.is_active = 1
                    bom_doc.flags.ignore_validate_update_after_submit = True
                    bom_doc.save(ignore_permissions=True)
                    if bom_doc.docstatus == 0:
                        bom_doc.submit()

                    if frappe.db.has_column("Item", "restaurant_bom_template") and item_doc.get("restaurant_bom_template") != bom_doc.name:
                        item_doc.db_set("restaurant_bom_template", bom_doc.name, update_modified=False)
                    if frappe.db.has_column("Item", "default_bom") and item_doc.get("default_bom") != bom_doc.name:
                        item_doc.db_set("default_bom", bom_doc.name, update_modified=False)
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"Legacy customization cleanup failed for {item_name}")

    _remove_legacy_custom_fields()
    frappe.clear_cache()
    frappe.db.commit()
