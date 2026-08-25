import frappe
from frappe import _
from frappe.utils import cint, flt


def _normalize_meta(selection_mode, required, min_select, max_select):
    mode = (selection_mode or "single").strip().lower() or "single"
    if mode not in {"single", "multi"}:
        mode = "single"

    reqd = cint(required)
    min_count = cint(min_select)
    max_count = cint(max_select or 1)
    if mode == "single":
        min_count = 1 if reqd else 0
        max_count = 1
    else:
        min_count = max(min_count, 0)
        max_count = max(max_count, 1)

    return mode, reqd, min_count, max_count


def _ensure_modifier_option_row(group_doc, payload):
    option_name = (payload.get("option_name") or "").strip()
    if not option_name:
        return False

    for row in group_doc.get("options") or []:
        if (row.get("option_name") or "").strip() == option_name:
            changed = False
            if (row.get("action_type") or "add_on").strip() != (payload.get("action_type") or "add_on").strip():
                row.action_type = payload.get("action_type") or "add_on"
                changed = True
            if (row.get("option_item") or "").strip() != (payload.get("option_item") or "").strip():
                row.option_item = payload.get("option_item") or ""
                changed = True
            if (row.get("alternative_bom") or "").strip() != (payload.get("alternative_bom") or "").strip():
                row.alternative_bom = payload.get("alternative_bom") or ""
                changed = True
            if flt(row.get("option_qty") or 1) != flt(payload.get("option_qty") or 1):
                row.option_qty = flt(payload.get("option_qty") or 1)
                changed = True
            if flt(row.get("price_delta") or 0) != flt(payload.get("price_delta") or 0):
                row.price_delta = flt(payload.get("price_delta") or 0)
                changed = True
            if flt(row.get("recipe_multiplier") or 1) != flt(payload.get("recipe_multiplier") or 1):
                row.recipe_multiplier = flt(payload.get("recipe_multiplier") or 1)
                changed = True
            if cint(row.get("is_default") or 0) != cint(payload.get("is_default") or 0):
                row.is_default = cint(payload.get("is_default") or 0)
                changed = True
            if cint(row.get("sort_order") or 0) != cint(payload.get("sort_order") or 0):
                row.sort_order = cint(payload.get("sort_order") or 0)
                changed = True
            if cint(row.get("is_active") or 1) != cint(payload.get("is_active") or 1):
                row.is_active = cint(payload.get("is_active") or 1)
                changed = True
            return changed

    group_doc.append(
        "options",
        {
            "option_name": option_name,
            "action_type": payload.get("action_type") or "add_on",
            "option_item": payload.get("option_item") or "",
            "alternative_bom": payload.get("alternative_bom") or "",
            "option_qty": flt(payload.get("option_qty") or 1),
            "price_delta": flt(payload.get("price_delta") or 0),
            "recipe_multiplier": flt(payload.get("recipe_multiplier") or 1),
            "is_default": cint(payload.get("is_default") or 0),
            "sort_order": cint(payload.get("sort_order") or 0),
            "is_active": cint(payload.get("is_active") if payload.get("is_active") not in ("", None) else 1),
        },
    )
    return True


def _ensure_modifier_group(meta, option_payloads):
    title = (meta.get("group_title") or meta.get("group_key") or "").strip()
    if not title:
        return ""

    existing = frappe.db.get_value("Restaurant Modifier Group", {"title": title}, "name")
    if existing:
        group_doc = frappe.get_doc("Restaurant Modifier Group", existing)
    else:
        group_doc = frappe.get_doc({"doctype": "Restaurant Modifier Group", "title": title})

    mode, reqd, min_count, max_count = _normalize_meta(
        meta.get("selection_mode"),
        meta.get("required"),
        meta.get("min_select"),
        meta.get("max_select"),
    )

    changed = False
    if (group_doc.get("selection_mode") or "single") != mode:
        group_doc.selection_mode = mode
        changed = True
    if cint(group_doc.get("required") or 0) != reqd:
        group_doc.required = reqd
        changed = True
    if cint(group_doc.get("min_select") or 0) != min_count:
        group_doc.min_select = min_count
        changed = True
    if cint(group_doc.get("max_select") or 1) != max_count:
        group_doc.max_select = max_count
        changed = True
    if cint(group_doc.get("is_active") if group_doc.get("is_active") not in ("", None) else 1) != 1:
        group_doc.is_active = 1
        changed = True

    for option_payload in option_payloads:
        changed = _ensure_modifier_option_row(group_doc, option_payload) or changed

    if group_doc.is_new():
        if not group_doc.get("options"):
            return ""
        group_doc.insert(ignore_permissions=True)
    elif changed:
        group_doc.save(ignore_permissions=True)

    return group_doc.name


def _ensure_item_alternative(base_item_code, alternative_item_code):
    base_item_code = (base_item_code or "").strip()
    alternative_item_code = (alternative_item_code or "").strip()
    if not base_item_code or not alternative_item_code:
        return
    if not frappe.db.exists("Item", base_item_code) or not frappe.db.exists("Item", alternative_item_code):
        return

    if frappe.db.exists(
        "Item Alternative",
        {"item_code": base_item_code, "alternative_item_code": alternative_item_code},
    ):
        return

    doc = frappe.get_doc(
        {
            "doctype": "Item Alternative",
            "item_code": base_item_code,
            "alternative_item_code": alternative_item_code,
            "two_way": 0,
        }
    )
    doc.insert(ignore_permissions=True)


def _migrate_bom_doc(bom_doc):
    rows = sorted(
        (bom_doc.get("restaurant_modifier_rows") or []),
        key=lambda d: (cint(d.get("sort_order") or 0), cint(d.get("idx") or 0)),
    )
    if not rows:
        return False

    group_meta_by_key = {}
    group_options_by_key = {}
    linked_groups = []
    linked_seen = set()
    replacement_mapped = False

    for row in rows:
        if cint(row.get("is_active")) == 0:
            continue

        linked_group = (row.get("modifier_group") or "").strip()
        if linked_group:
            if linked_group not in linked_seen:
                linked_seen.add(linked_group)
                linked_groups.append(
                    {
                        "modifier_group": linked_group,
                        "required": cint(row.get("required")),
                        "min_select": cint(row.get("min_select")),
                        "max_select": cint(row.get("max_select") or 1),
                        "sort_order": cint(row.get("sort_order") or 0),
                        "is_active": 1,
                    }
                )
            continue

        legacy_group_key = (row.get("group_key") or row.get("group_title") or "").strip()
        if not legacy_group_key:
            continue

        if legacy_group_key not in group_meta_by_key:
            group_meta_by_key[legacy_group_key] = {
                "group_key": legacy_group_key,
                "group_title": (row.get("group_title") or legacy_group_key).strip(),
                "selection_mode": (row.get("selection_mode") or "single").strip() or "single",
                "required": cint(row.get("required")),
                "min_select": cint(row.get("min_select")),
                "max_select": cint(row.get("max_select") or 1),
            }
            group_options_by_key[legacy_group_key] = []

        option_name = (
            row.get("option_key")
            or row.get("option_label")
            or row.get("option_item")
            or row.get("alternative_bom")
            or ""
        ).strip()
        if not option_name:
            continue

        raw_modifier_type = (row.get("modifier_type") or "add_on").strip() or "add_on"
        option_item = (row.get("option_item") or "").strip()
        replacement_for_item = (row.get("replacement_for_item") or "").strip()
        alternative_bom = (row.get("alternative_bom") or "").strip()

        if raw_modifier_type == "replacement":
            if replacement_for_item and option_item:
                for bom_row in bom_doc.get("items") or []:
                    if (bom_row.get("item_code") or "").strip() == replacement_for_item:
                        if bom_row.get("allow_alternative_item") != 1:
                            bom_row.allow_alternative_item = 1
                            replacement_mapped = True
                        _ensure_item_alternative(replacement_for_item, option_item)
                        break
            continue

        action_type = "bom_variant" if raw_modifier_type == "bom_variant" else "add_on"
        option_payload = {
            "option_name": option_name,
            "action_type": action_type,
            "option_item": option_item if action_type == "add_on" else "",
            "alternative_bom": alternative_bom if action_type == "bom_variant" else "",
            "option_qty": flt(row.get("option_qty") or 1),
            "price_delta": flt(row.get("price_delta") or 0),
            "recipe_multiplier": flt(row.get("recipe_multiplier") or 1),
            "is_default": cint(row.get("is_default") or 0),
            "sort_order": cint(row.get("sort_order") or 0),
            "is_active": 1,
        }

        existing_names = {(entry.get("option_name") or "").strip() for entry in group_options_by_key[legacy_group_key]}
        if option_name not in existing_names:
            group_options_by_key[legacy_group_key].append(option_payload)

    for group_key, group_meta in group_meta_by_key.items():
        option_payloads = group_options_by_key.get(group_key) or []
        group_name = _ensure_modifier_group(group_meta, option_payloads)
        if not group_name or group_name in linked_seen:
            continue

        linked_seen.add(group_name)
        linked_groups.append(
            {
                "modifier_group": group_name,
                "required": cint(group_meta.get("required")),
                "min_select": cint(group_meta.get("min_select")),
                "max_select": cint(group_meta.get("max_select") or 1),
                "sort_order": cint(linked_groups[-1]["sort_order"] + 1) if linked_groups else 0,
                "is_active": 1,
            }
        )

    if not linked_groups and not replacement_mapped:
        return False

    bom_doc.set("restaurant_modifier_rows", [])
    for payload in sorted(linked_groups, key=lambda d: (cint(d.get("sort_order") or 0), d.get("modifier_group") or "")):
        bom_doc.append("restaurant_modifier_rows", payload)

    if bom_doc.docstatus == 1:
        bom_doc.flags.ignore_validate_update_after_submit = True
    bom_doc.save(ignore_permissions=True)
    return True


def execute():
    if not frappe.db.exists("DocType", "BOM"):
        return
    if not frappe.get_meta("BOM").has_field("restaurant_modifier_rows"):
        return
    if not frappe.db.exists("DocType", "Restaurant Modifier Group"):
        return
    if not frappe.db.exists("DocType", "Restaurant Modifier Option"):
        return

    changed_count = 0
    for bom_name in frappe.get_all("BOM", pluck="name", ignore_permissions=True):
        try:
            bom_doc = frappe.get_doc("BOM", bom_name)
            if _migrate_bom_doc(bom_doc):
                changed_count += 1
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                _("Failed BOM modifier group-link migration for BOM {0}").format(bom_name),
            )

    if changed_count:
        frappe.clear_cache()
    frappe.db.commit()
