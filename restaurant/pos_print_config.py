"""Shared, side-effect-free normalization for POS printer profiles."""


def _as_int(value, default=0):
    if isinstance(value, bool):
        return int(value)
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def clean_management_pos_print_profiles(profiles):
    if not isinstance(profiles, list):
        return []

    cleaned = []
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        kind = str(profile.get("kind") or "").strip().lower()
        if kind not in ("customer", "kitchen", "bar"):
            kind = "kitchen"

        label = str(profile.get("label") or "").strip()
        item_groups = profile.get("item_groups") or []
        if not isinstance(item_groups, list):
            item_groups = []

        width = _as_int(profile.get("paper_width_mm"), 0)
        copies = _as_int(profile.get("copies"), 0)
        cleaned.append({
            "label": label or ("چاپ مشتری" if kind == "customer" else "چاپ آشپزخانه"),
            "kind": kind,
            "printer_name": str(profile.get("printer_name") or "").strip(),
            "item_groups": [str(group).strip() for group in item_groups if group is not None and str(group).strip()],
            "paper_width_mm": width if width in (58, 80) else 0,
            "copies": min(10, max(0, copies)),
            "auto_print": _as_int(profile.get("auto_print"), 1 if kind == "customer" else 0),
            "show_prices": _as_int(profile.get("show_prices"), 1 if kind == "customer" else 0),
            "enabled": _as_int(profile.get("enabled"), 1),
        })
    return cleaned
