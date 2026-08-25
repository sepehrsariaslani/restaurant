---
name: Backend 500 from missing helper function
description: set_management_site_settings called _has_doctype_field which was never defined — fix pattern for adding new fields to backend
---

## The bug
`set_management_site_settings` in `restaurant/api.py` called `_has_doctype_field("Restaurant Web Settings", fieldname)` on every field it tried to save. This function did not exist in the file → Python raised `NameError: name '_has_doctype_field' is not defined` → Frappe returned 500 INTERNAL SERVER ERROR.

**Why:** The function was referenced but never implemented, likely cut during a refactor.

## Fix applied
Added `_has_doctype_field(doctype, fieldname)` near `_has_column` (around line 2207):
```python
def _has_doctype_field(doctype, fieldname):
    try:
        meta = frappe.get_meta(doctype)
        if meta.has_field(fieldname):
            return True
        return bool(frappe.db.get_value("Custom Field", {"dt": doctype, "fieldname": fieldname}, "name"))
    except Exception:
        return False
```

## Pattern for adding new frontend fields to backend
When adding new frontend `webSettings` fields that should persist to `Restaurant Web Settings`:
1. Add to `scalar_fields` list inside `set_management_site_settings`
2. Add a `_ensure_display_variant_setting_fields()` style function that creates the Custom Field if missing
3. Call that ensure function inside both `set_management_site_settings` and `_management_site_settings_payload`
4. Add the field to the `web_settings` dict in `_management_site_settings_payload` (both try and except blocks)

**How to apply:** Any time a new string setting is added to the management UI, follow all four steps above or the field will be silently ignored on save and missing on load.
