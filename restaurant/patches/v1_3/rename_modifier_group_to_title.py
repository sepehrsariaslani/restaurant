import frappe


def _next_available_name(base_name, current_name):
    candidate = base_name
    counter = 2
    while frappe.db.exists("Restaurant Modifier Group", candidate) and candidate != current_name:
        candidate = f"{base_name}-{counter}"
        counter += 1
    return candidate


def execute():
    if not frappe.db.exists("DocType", "Restaurant Modifier Group"):
        return

    rows = frappe.get_all(
        "Restaurant Modifier Group",
        fields=["name", "title"],
        ignore_permissions=True,
        order_by="modified asc",
    )

    renamed = 0
    for row in rows:
        title = (row.get("title") or "").strip()
        current_name = (row.get("name") or "").strip()
        if not title or not current_name or title == current_name:
            continue

        target = _next_available_name(title, current_name)
        if target == current_name:
            continue

        try:
            frappe.rename_doc(
                "Restaurant Modifier Group",
                current_name,
                target,
                force=True,
                merge=False,
                ignore_permissions=True,
            )
            renamed += 1
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Failed renaming Restaurant Modifier Group {current_name} to {target}",
            )

    if renamed:
        frappe.clear_cache()
        frappe.db.commit()
