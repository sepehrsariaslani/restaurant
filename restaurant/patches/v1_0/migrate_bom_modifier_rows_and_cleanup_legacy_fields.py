import json

import frappe
from frappe.utils import cint, flt


BOM_CUSTOM_FIELDS = [
    {
        "fieldname": "restaurant_modifier_rows",
        "label": "Restaurant Modifier Rows",
        "fieldtype": "Table",
        "options": "Restaurant BOM Modifier",
        "insert_after": "description",
    },
    {
        "fieldname": "restaurant_menu_item_ref",
        "label": "Restaurant Menu Item Ref",
        "fieldtype": "Link",
        "options": "Item",
        "insert_after": "restaurant_modifier_rows",
    },
]

LEGACY_FIELDS = {
    "Item": [
        "restaurant_ingredients",
        "restaurant_modifier_groups",
        "restaurant_bom_template",
        "restaurant_recipe_yield_qty",
        "restaurant_recipe_uom",
    ],
    "BOM": [
        "restaurant_modifier_groups_json",
    ],
    "Item Alternative": [
        "restaurant_modifier_group",
        "restaurant_modifier_group_title",
        "restaurant_selection_mode",
        "restaurant_required",
        "restaurant_min_select",
        "restaurant_max_select",
        "restaurant_price_delta",
        "restaurant_recipe_multiplier",
        "restaurant_is_default_modifier",
        "restaurant_is_modifier_option",
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


def _append_modifier_row_if_missing(bom_doc, payload):
    group_key = (payload.get("group_key") or "").strip()
    option_key = (payload.get("option_key") or "").strip()
    modifier_type = (payload.get("modifier_type") or "add_on").strip()
    if not group_key or not option_key:
        return False

    for row in bom_doc.get("restaurant_modifier_rows") or []:
        if (
            (row.get("group_key") or "").strip() == group_key
            and (row.get("option_key") or "").strip() == option_key
            and (row.get("modifier_type") or "add_on").strip() == modifier_type
        ):
            return False

    bom_doc.append("restaurant_modifier_rows", payload)
    return True


def _rows_from_json_group(group, sort_index=0):
    group_key = (group.get("group_name") or group.get("title") or "").strip()
    group_title = (group.get("title") or group_key).strip()
    selection_mode = (group.get("selection_mode") or "single").strip() or "single"
    required = cint(group.get("required"))
    min_select = cint(group.get("min_select"))
    max_select = cint(group.get("max_select") or 1)

    if selection_mode == "single":
        min_select = 1 if required else 0
        max_select = 1
    else:
        min_select = max(min_select, 0)
        max_select = max(max_select, 1)

    rows = []
    for idx, option in enumerate(group.get("options") or [], start=1):
        option_key = (option.get("name") or "").strip()
        if not option_key:
            continue

        option_item = option_key if frappe.db.exists("Item", option_key) else ""
        alternative_bom = option_key if frappe.db.exists("BOM", option_key) else ""
        modifier_type = "bom_variant" if alternative_bom else "add_on"

        rows.append(
            {
                "group_key": group_key,
                "group_title": group_title,
                "selection_mode": selection_mode,
                "required": required,
                "min_select": min_select,
                "max_select": max_select,
                "modifier_type": modifier_type,
                "option_key": option_key,
                "option_label": option_key,
                "option_item": option_item,
                "alternative_bom": alternative_bom,
                "option_qty": 1,
                "price_delta": flt(option.get("price_delta")),
                "recipe_multiplier": flt(option.get("recipe_multiplier") or 1),
                "is_default": cint(option.get("is_default")),
                "sort_order": sort_index * 1000 + idx,
                "is_active": 1,
            }
        )

    return rows


def _rows_from_item_alternative(item_code):
    if not frappe.db.exists("DocType", "Item Alternative"):
        return []

    filters = {"item_code": item_code}
    fields = ["alternative_item_code"]

    if frappe.db.has_column("Item Alternative", "restaurant_is_modifier_option"):
        filters["restaurant_is_modifier_option"] = 1
        fields.extend(
            [
                "restaurant_modifier_group",
                "restaurant_modifier_group_title",
                "restaurant_selection_mode",
                "restaurant_required",
                "restaurant_min_select",
                "restaurant_max_select",
                "restaurant_price_delta",
                "restaurant_recipe_multiplier",
                "restaurant_is_default_modifier",
            ]
        )

    rows = frappe.get_all(
        "Item Alternative",
        filters=filters,
        fields=fields,
        ignore_permissions=True,
    )

    payload_rows = []
    for idx, row in enumerate(rows, start=1):
        option_item = (row.get("alternative_item_code") or "").strip()
        if not option_item:
            continue

        group_key = (row.get("restaurant_modifier_group") or row.get("restaurant_modifier_group_title") or "default").strip()
        group_title = (row.get("restaurant_modifier_group_title") or group_key).strip()
        selection_mode = (row.get("restaurant_selection_mode") or "single").strip() or "single"
        required = cint(row.get("restaurant_required"))
        min_select = cint(row.get("restaurant_min_select"))
        max_select = cint(row.get("restaurant_max_select") or 1)

        if selection_mode == "single":
            min_select = 1 if required else 0
            max_select = 1
        else:
            min_select = max(min_select, 0)
            max_select = max(max_select, 1)

        payload_rows.append(
            {
                "group_key": group_key,
                "group_title": group_title,
                "selection_mode": selection_mode,
                "required": required,
                "min_select": min_select,
                "max_select": max_select,
                "modifier_type": "add_on",
                "option_key": option_item,
                "option_label": option_item,
                "option_item": option_item,
                "option_qty": 1,
                "price_delta": flt(row.get("restaurant_price_delta")),
                "recipe_multiplier": flt(row.get("restaurant_recipe_multiplier") or 1),
                "is_default": cint(row.get("restaurant_is_default_modifier")),
                "sort_order": idx,
                "is_active": 1,
            }
        )

    return payload_rows


def _migrate_bom_modifier_rows():
    if not frappe.db.exists("DocType", "BOM"):
        return
    if not frappe.get_meta("BOM").has_field("restaurant_modifier_rows"):
        return

    for bom_name in frappe.get_all("BOM", pluck="name", ignore_permissions=True):
        try:
            bom_doc = frappe.get_doc("BOM", bom_name)
            changed = False

            # 1) JSON payload -> table rows
            json_payload = []
            if frappe.db.has_column("BOM", "restaurant_modifier_groups_json"):
                raw_json = (bom_doc.get("restaurant_modifier_groups_json") or "").strip()
                if raw_json:
                    try:
                        parsed = json.loads(raw_json)
                        if isinstance(parsed, list):
                            json_payload = parsed
                    except Exception:
                        pass

            for g_idx, group in enumerate(json_payload, start=1):
                if not isinstance(group, dict):
                    continue
                for payload in _rows_from_json_group(group, g_idx):
                    changed = _append_modifier_row_if_missing(bom_doc, payload) or changed

            # 2) legacy Item Alternative metadata -> table rows
            if bom_doc.item:
                for payload in _rows_from_item_alternative(bom_doc.item):
                    changed = _append_modifier_row_if_missing(bom_doc, payload) or changed

            if changed:
                bom_doc.flags.ignore_validate_update_after_submit = True
                bom_doc.save(ignore_permissions=True)

        except Exception:
            frappe.log_error(frappe.get_traceback(), f"Failed to migrate BOM modifier rows for {bom_name}")


def _remove_custom_field_if_exists(dt, fieldname):
    name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname}, "name")
    if not name:
        return
    try:
        frappe.delete_doc("Custom Field", name, ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Failed to delete custom field {dt}.{fieldname}")


def _sync_bom_defaults_from_legacy_template():
    if not frappe.db.exists("DocType", "Item"):
        return
    if not frappe.db.has_column("Item", "restaurant_bom_template"):
        return

    rows = frappe.get_all(
        "Item",
        filters={"restaurant_bom_template": ["!=", ""]},
        fields=["name", "default_bom", "restaurant_bom_template"],
        ignore_permissions=True,
    )
    for row in rows:
        template = (row.get("restaurant_bom_template") or "").strip()
        if not template or not frappe.db.exists("BOM", template):
            continue

        if frappe.db.has_column("BOM", "is_default") and not cint(
            frappe.db.get_value("BOM", template, "is_default") or 0
        ):
            frappe.db.set_value("BOM", template, "is_default", 1, update_modified=False)

        # The Restaurant runtime now resolves BOM by BOM.is_default and no longer
        # depends on Item.default_bom links.
        if frappe.db.has_column("Item", "default_bom") and (row.get("default_bom") or "").strip():
            frappe.db.set_value("Item", row.name, "default_bom", "", update_modified=False)


def _cleanup_legacy_fields():
    for dt, fieldnames in LEGACY_FIELDS.items():
        for fieldname in fieldnames:
            _remove_custom_field_if_exists(dt, fieldname)


def execute():
    if frappe.db.exists("DocType", "Restaurant BOM Modifier"):
        for field_def in BOM_CUSTOM_FIELDS:
            _ensure_custom_field("BOM", field_def)

    _migrate_bom_modifier_rows()
    _sync_bom_defaults_from_legacy_template()
    _cleanup_legacy_fields()
    frappe.clear_cache()
    frappe.db.commit()

