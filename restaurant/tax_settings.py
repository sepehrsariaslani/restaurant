"""Company-scoped Moadian settings backed by the native Company record."""

import unicodedata
from urllib.parse import urlsplit

import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.password import get_decrypted_password, set_encrypted_password


SINGLETON_DOCTYPE = "Restaurant Web Settings"
SINGLETON_NAME = "Restaurant Web Settings"
TOKEN_FIELD = "restaurant_tax_auth_token"
COMPANY_FIELDS = {
    "enabled": "custom_moadian_enabled",
    "sandbox": "custom_moadian_sandbox",
    "api_url": "custom_moadian_api_url",
    "memory_code": "custom_moadian_memory_code",
    "auth_token": "custom_moadian_auth_token",
    "economic_code": "custom_moadian_economic_code",
    "auto_submit": "custom_moadian_auto_submit",
}
LEGACY_FIELD_MAP = {
    "restaurant_tax_enabled": "enabled",
    "restaurant_tax_sandbox": "sandbox",
    "restaurant_tax_api_url": "api_url",
    "restaurant_tax_memory_code": "memory_code",
    "restaurant_tax_auth_token": "auth_token",
    "restaurant_tax_economic_code": "economic_code",
    "restaurant_tax_auto_submit": "auto_submit",
}


def _digits_only(value):
    digits = []
    for character in str(value or ""):
        try:
            digits.append(str(unicodedata.digit(character)))
        except (TypeError, ValueError):
            if character.isdigit():
                digits.append(character)
    return "".join(digits)


def _tax_ensure_ops_ready():
    try:
        from restaurant import api_feature_pack

        ensure_fields = getattr(api_feature_pack, "_fp_ensure_custom_fields", None)
        if not callable(ensure_fields):
            raise RuntimeError("api_feature_pack helper missing: _fp_ensure_custom_fields")
        ensure_fields(
            SINGLETON_DOCTYPE,
            [
                {"fieldname": "restaurant_tax_section", "label": "سامانه مودیان", "fieldtype": "Section Break"},
                {"fieldname": "restaurant_tax_enabled", "label": "اتصال سامانه مودیان فعال", "fieldtype": "Check", "default": "0"},
                {"fieldname": "restaurant_tax_sandbox", "label": "حالت آزمایشی (محیط تست)", "fieldtype": "Check", "default": "1"},
                {"fieldname": "restaurant_tax_column", "label": "", "fieldtype": "Column Break"},
                {"fieldname": "restaurant_tax_api_url", "label": "نشانی سرویس ارسال صورتحساب", "fieldtype": "Data"},
                {"fieldname": "restaurant_tax_memory_code", "label": "کد حافظه مالیاتی", "fieldtype": "Data"},
                {"fieldname": TOKEN_FIELD, "label": "توکن احراز هویت", "fieldtype": "Password"},
                {"fieldname": "restaurant_tax_economic_code", "label": "کد اقتصادی", "fieldtype": "Data"},
                {"fieldname": "restaurant_tax_auto_submit", "label": "ارسال خودکار روزانه فاکتورها", "fieldtype": "Check", "default": "0"},
            ],
            anchor_candidates=["restaurant_reservation_section", "restaurant_delivery_section", "restaurant_club_section", "configuration_tab"],
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Restaurant tax ensure fields failed")


def _legacy_auth_token():
    try:
        raw_value = frappe.db.get_single_value(SINGLETON_DOCTYPE, TOKEN_FIELD, cache=False)
    except Exception:
        raw_value = None
    raw_value = str(raw_value or "").strip()
    if raw_value and set(raw_value) != {"*"}:
        # Older Accounts/Restaurant writers stored Password fields directly in
        # Singles. Read that legacy value so it can be re-encrypted on save.
        return raw_value
    try:
        return get_decrypted_password(
            SINGLETON_DOCTYPE,
            SINGLETON_NAME,
            TOKEN_FIELD,
            raise_exception=False,
        ) or ""
    except Exception:
        return ""


def _tax_setting(fieldname, default=None):
    if fieldname == TOKEN_FIELD:
        return _legacy_auth_token() or default
    try:
        value = frappe.db.get_single_value(SINGLETON_DOCTYPE, fieldname, cache=False)
        return default if value in (None, "") else value
    except Exception:
        return default


def _site_settings(include_auth_token=False):
    token = _legacy_auth_token()
    settings = {
        "enabled": cint(_tax_setting("restaurant_tax_enabled", 0)) == 1,
        "sandbox": cint(_tax_setting("restaurant_tax_sandbox", 1)) == 1,
        "api_url": str(_tax_setting("restaurant_tax_api_url", "") or "").strip(),
        "memory_code": str(_tax_setting("restaurant_tax_memory_code", "") or "").strip(),
        "token_set": bool(token),
        "economic_code": str(_tax_setting("restaurant_tax_economic_code", "") or "").strip(),
        "auto_submit": cint(_tax_setting("restaurant_tax_auto_submit", 0)) == 1,
        "economic_code_matches_company": False,
        "settings_are_site_wide": True,
        "settings_scope": "site-wide",
    }
    if include_auth_token:
        settings["auth_token"] = token
    return settings


def _company_scope_available():
    if not frappe.db.exists("DocType", "Company"):
        return False
    meta = frappe.get_meta("Company")
    return all(meta.has_field(fieldname) for fieldname in COMPANY_FIELDS.values())


def _legacy_matches_company(company_doc, legacy_settings):
    company_tax_id = _digits_only(company_doc.get("tax_id"))
    economic_code = _digits_only(legacy_settings.get("economic_code"))
    if not company_tax_id or company_tax_id != economic_code:
        return False

    matches_by_tax_id = getattr(frappe.local, "moadian_companies_by_tax_id", None)
    if matches_by_tax_id is None:
        matches_by_tax_id = {}
        company_rows = frappe.get_all("Company", fields=["name", "tax_id"], limit_page_length=0)
        for row in company_rows:
            normalized = _digits_only(row.get("tax_id"))
            if normalized:
                matches_by_tax_id.setdefault(normalized, []).append(row.name)
        frappe.local.moadian_companies_by_tax_id = matches_by_tax_id

    matches = matches_by_tax_id.get(company_tax_id, [])
    return matches == [company_doc.name]


def _company_settings(company_doc, include_auth_token=False):
    if not _company_scope_available():
        return None

    token = company_doc.get_password(COMPANY_FIELDS["auth_token"], raise_exception=False) or ""
    settings = {
        "enabled": cint(company_doc.get(COMPANY_FIELDS["enabled"])),
        "sandbox": cint(company_doc.get(COMPANY_FIELDS["sandbox"])) == 1,
        "api_url": str(company_doc.get(COMPANY_FIELDS["api_url"]) or "").strip(),
        "memory_code": str(company_doc.get(COMPANY_FIELDS["memory_code"]) or "").strip(),
        "token_set": bool(token),
        "economic_code": str(company_doc.get(COMPANY_FIELDS["economic_code"]) or "").strip(),
        "auto_submit": cint(company_doc.get(COMPANY_FIELDS["auto_submit"])) == 1,
        "economic_code_matches_company": _digits_only(company_doc.get("tax_id"))
        == _digits_only(company_doc.get(COMPANY_FIELDS["economic_code"])),
        "settings_are_site_wide": False,
        "settings_scope": "company",
    }
    configured = any(
        settings[field]
        for field in ("enabled", "api_url", "memory_code", "token_set", "economic_code", "auto_submit")
    )
    if include_auth_token:
        settings["auth_token"] = token
    return settings if configured else None


def _empty_company_settings(company_doc):
    return {
        "enabled": False,
        "sandbox": True,
        "api_url": "",
        "memory_code": "",
        "token_set": False,
        "economic_code": "",
        "auto_submit": False,
        "economic_code_matches_company": False,
        "settings_are_site_wide": False,
        "settings_scope": "company",
    }


def _tax_settings(company=None, include_auth_token=False):
    if not company:
        return _site_settings(include_auth_token=include_auth_token)

    company_doc = frappe.get_cached_doc("Company", company)
    scoped = _company_settings(company_doc, include_auth_token=include_auth_token)
    if scoped:
        return scoped

    legacy = _site_settings(include_auth_token=include_auth_token)
    legacy["economic_code_matches_company"] = _legacy_matches_company(company_doc, legacy)
    if legacy["economic_code_matches_company"]:
        legacy["settings_are_site_wide"] = True
        legacy["settings_scope"] = "legacy-site-wide"
        return legacy

    return _empty_company_settings(company_doc)


def _save_company_settings(company, payload):
    if not _company_scope_available():
        frappe.throw(
            _("تنظیمات مؤدیانِ جداگانه برای هر شرکت پس از به‌روزرسانی Restaurant فعال می‌شود"),
            frappe.ValidationError,
        )

    doc = frappe.get_doc("Company", company)
    previous_company_settings = _company_settings(doc, include_auth_token=True) or _empty_company_settings(doc)
    legacy = _site_settings(include_auth_token=True)
    legacy_matches = _legacy_matches_company(doc, legacy)

    for legacy_field, setting_name in LEGACY_FIELD_MAP.items():
        if legacy_field not in payload or setting_name == "auth_token":
            continue
        doc.set(COMPANY_FIELDS[setting_name], payload[legacy_field])

    submitted_token = str(payload.get("restaurant_tax_auth_token") or "").strip()
    current_token = previous_company_settings.get("auth_token") or ""
    legacy_token_migrated = False
    if submitted_token:
        doc.set(COMPANY_FIELDS["auth_token"], submitted_token)
    elif not current_token and legacy_matches:
        legacy_token = legacy.get("auth_token") or ""
        if legacy_token:
            doc.set(COMPANY_FIELDS["auth_token"], legacy_token)
            legacy_token_migrated = True

    company_tax_id = _digits_only(doc.get("tax_id"))
    economic_code = _digits_only(doc.get(COMPANY_FIELDS["economic_code"]))
    if not company_tax_id or not economic_code or company_tax_id != economic_code:
        frappe.throw(_("کد اقتصادی باید با Tax ID همین شرکت یکسان باشد"), frappe.ValidationError)

    endpoint_value = str(doc.get(COMPANY_FIELDS["api_url"]) or "").strip()
    if endpoint_value:
        try:
            endpoint = urlsplit(endpoint_value)
        except ValueError:
            endpoint = None
        if (
            not endpoint
            or endpoint.scheme.lower() != "https"
            or not endpoint.hostname
            or endpoint.username
            or endpoint.password
            or endpoint.fragment
        ):
            frappe.throw(_("نشانی سرویس باید HTTPS باشد و اطلاعات ورود در خود نشانی قرار نگیرد"), frappe.ValidationError)

    if cint(doc.get(COMPANY_FIELDS["enabled"])):
        token = submitted_token or current_token or (legacy.get("auth_token") if legacy_matches else "")
        if not endpoint_value or not token or not str(doc.get(COMPANY_FIELDS["memory_code"]) or "").strip():
            frappe.throw(_("برای فعال‌کردن اتصال، نشانی HTTPS، کد حافظه و توکن لازم است"), frappe.ValidationError)

    doc.save(ignore_permissions=True)
    return {
        "status": "success",
        "settings": _tax_settings(doc.name),
        "legacy_settings_migrated": legacy_token_migrated,
    }


def _save_tax_settings(payload=None, company=None):
    """Save legacy site settings or company-scoped settings through native records."""
    _tax_ensure_ops_ready()
    if isinstance(payload, str):
        payload = frappe.parse_json(payload)
    payload = payload or {}
    if not isinstance(payload, dict):
        frappe.throw(_("تنظیمات اتصال نامعتبر است"), frappe.ValidationError)

    if company:
        return _save_company_settings(company, payload)

    for key in ("restaurant_tax_enabled", "restaurant_tax_sandbox", "restaurant_tax_auto_submit"):
        if key in payload:
            frappe.db.set_single_value(SINGLETON_DOCTYPE, key, cint(payload.get(key)), update_modified=False)
    for key in ("restaurant_tax_api_url", "restaurant_tax_memory_code", "restaurant_tax_economic_code"):
        if key in payload:
            frappe.db.set_single_value(SINGLETON_DOCTYPE, key, str(payload.get(key) or "").strip(), update_modified=False)
    if "restaurant_tax_auth_token" in payload and str(payload.get("restaurant_tax_auth_token") or "").strip():
        token = str(payload["restaurant_tax_auth_token"]).strip()
        set_encrypted_password(SINGLETON_DOCTYPE, SINGLETON_NAME, token, TOKEN_FIELD)
        frappe.db.set_single_value(SINGLETON_DOCTYPE, TOKEN_FIELD, "*" * len(token), update_modified=False)
    return {"status": "success", "settings": _site_settings()}
