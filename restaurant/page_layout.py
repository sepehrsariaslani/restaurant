"""Per-company page layout storage for the block-based public site.

The restaurant app is a companion to ERPNext where every branch is
modelled as its own Company. The home page (and later, other pages) is
described as an ordered array of blocks. We persist that array as a JSON
blob in a Frappe global default keyed by company, so each branch keeps
its own independent design.

Storage key format:  restaurant_page_layout_v1::<company>

Public surface:
    - get_page_layout(page="home", company=None)        -> dict
    - set_management_page_layout(payload, company=None)  -> dict (whitelisted)
    - get_management_page_layout(page, company)          -> dict (whitelisted)
    - reset_management_page_layout(page, company)        -> dict (whitelisted)

The blob shape is intentionally permissive; the frontend registry is the
source of truth for which block types / variants are valid, and it
normalizes anything unexpected at render time.
"""

import json
import hashlib
import re
import math

import frappe
from frappe import _

PAGE_LAYOUT_KEY_PREFIX = "restaurant_page_layout_v1"
PUBLIC_EXTENSION_PAGES = {
	"blog", "blog-post", "menu", "item", "cart", "customize", "bom-preview",
	"payment", "payment-callback", "order-success", "order-start", "order-type",
	"order-dine-in", "order-pickup", "order-delivery", "customer-login", "survey",
	"customer-dashboard", "customer-referrals", "customer-collaboration",
	"customer-recurring-orders", "customer-nutrition", "customer-profile",
	"customer-vehicles", "customer-wallet", "customer-addresses", "customer-branches",
	"customer-orders", "customer-order-detail", "customer-delivery",
	"customer-table-reservation", "customer-table-select", "checkout", "payment-fail",
}
SUPPORTED_PAGES = {"home", "homev2", "about", "faq", "product_groups", *PUBLIC_EXTENSION_PAGES}
DEFAULT_PAGE = "home"

# Block types the backend is willing to store. Kept in sync with the
# frontend registry (blockRegistry.js). Unknown types are dropped so a
# stale/hostile payload can never inject arbitrary component names.
ALLOWED_BLOCK_TYPES = {
	"hero",
	"about",
	"products",
	"categories",
	"features",
	"faq",
	"banner",
	"popular",
	"healthy_hero",
	"section", "text", "image", "button", "spacer", "divider",
}

MAX_BLOCKS_PER_PAGE = 40


def _parse_json(value, default):
	if value is None:
		return default
	if isinstance(value, (dict, list)):
		return value
	if isinstance(value, str):
		stripped = value.strip()
		if not stripped:
			return default
		try:
			return json.loads(stripped)
		except Exception:
			return default
	return default


def resolve_company(company=None):
	"""Resolve the company (== branch) whose layout we should read/write.

	Preference order:
	  1. explicit argument
	  2. the user's default company (per-branch operators)
	  3. the global default company (single-branch installs)
	"""
	candidate = (company or "").strip()
	if candidate:
		return candidate

	try:
		user_company = (frappe.defaults.get_user_default("company") or "").strip()
		if user_company:
			return user_company
	except Exception:
		pass

	try:
		global_company = (frappe.defaults.get_global_default("company") or "").strip()
		if global_company:
			return global_company
	except Exception:
		pass

	return "__default__"


def _storage_key(company):
	resolved = resolve_company(company)
	return f"{PAGE_LAYOUT_KEY_PREFIX}::{resolved}"


def _normalize_page(page):
	value = (page or "").strip() or DEFAULT_PAGE
	if value in SUPPORTED_PAGES or re.fullmatch(r"custom:[a-z0-9][a-z0-9-]{0,79}", value):
		return value
	frappe.throw(_("صفحهٔ طراحی معتبر نیست."))


def _load_layout_doc(company, for_update=False):
	"""Return the full {page: {blocks: [...]}} map for a company."""
	if for_update:
		# Lock the authoritative defaults row until the request transaction ends.
		rows = frappe.db.sql("SELECT defvalue FROM `tabDefaultValue` WHERE parent='__global' AND defkey=%s FOR UPDATE", (_storage_key(company),))
		parsed = _parse_json(rows[0][0] if rows else None, {})
		return parsed if isinstance(parsed, dict) else {}
	try:
		raw = frappe.defaults.get_global_default(_storage_key(company))
	except Exception:
		raw = None
	parsed = _parse_json(raw, {})
	return parsed if isinstance(parsed, dict) else {}


def _save_layout_doc(company, doc):
	key = _storage_key(company)
	frame = json.dumps(doc, ensure_ascii=False)
	if len(frame.encode("utf-8")) > 900000:
		frappe.throw(_("حجم طراحی بیش از حد مجاز است؛ اندازهٔ متن‌ها و تعداد کامپوننت‌ها را کاهش دهید."))
	framppe_set_global_default(key, frame)


def framppe_set_global_default(key, value):
	# Small indirection so tests can patch it; Frappe API name kept intact.
	framppe = frappe
	framppe.db.set_global(key, value)


def _sanitize_block(raw, index, depth=0, budget=None, seen=None):
	if not isinstance(raw, dict) or depth > 4:
		return None
	budget = budget if budget is not None else [120]
	seen = seen if seen is not None else set()
	if budget[0] <= 0:
		return None
	budget[0] -= 1
	block_type = str(raw.get("type") or "").strip()
	if block_type not in ALLOWED_BLOCK_TYPES:
		return None

	props = raw.get("props")
	if not isinstance(props, dict):
		props = {}

	block_id = str(raw.get("id") or f"{block_type}_{index}").strip()
	if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", block_id) or block_id in seen:
		block_id = f"{block_type}_{index}_{len(seen)}"
	while block_id in seen:
		block_id = f"{block_id}_{len(seen)}"
	seen.add(block_id)

	return {
		"id": block_id,
		"type": block_type,
		"variant": str(raw.get("variant") or "").strip(),
		"enabled": 0 if str(raw.get("enabled")) in ("0", "false", "False") else 1,
		"order": index,
		"props": props,
		"name": str(raw.get("name") or "")[:100],
		"locked": raw.get("locked") in (True, 1, "1"),
		"design": _sanitize_design(raw.get("design")),
		"children": [block for child_index, child in enumerate((raw.get("children") or [])[:40])
			if (block := _sanitize_block(child, child_index, depth + 1, budget, seen))]
			if block_type == "section" and isinstance(raw.get("children"), list) else [],
	}


def _sanitize_blocks(blocks):
	if not isinstance(blocks, list):
		return []
	out = []
	budget = [120]
	seen = set()
	for index, raw in enumerate(blocks[:MAX_BLOCKS_PER_PAGE]):
		block = _sanitize_block(raw, index, budget=budget, seen=seen)
		if block:
			out.append(block)
	return out


def get_page_layout(page=DEFAULT_PAGE, company=None):
	"""Internal read used by the public boot. Never raises."""
	page = _normalize_page(page)
	doc = _load_layout_doc(company)
	page_doc = doc.get(page) if isinstance(doc, dict) else None
	blocks = _sanitize_blocks((page_doc or {}).get("blocks")) if isinstance(page_doc, dict) else []
	return {"page": page, "blocks": blocks, "stored": isinstance(page_doc, dict),
		"metadata": (page_doc or {}).get("metadata", {}), "revision": _revision(page_doc)}


def get_boot_page_layout(company=None):
	"""Return the {page: {blocks}} map for injection into boot.

	Only includes pages that actually have stored blocks, so the frontend
	fallback (buildLegacyLayout) still kicks in for undesigned pages.
	"""
	out = {}
	doc = _load_layout_doc(company)
	for page in doc:
		if page not in SUPPORTED_PAGES and not page.startswith("custom:"):
			continue
		page_doc = doc.get(page) if isinstance(doc, dict) else None
		blocks = _sanitize_blocks((page_doc or {}).get("blocks")) if isinstance(page_doc, dict) else []
		if page.startswith("custom:") and not (page_doc or {}).get("metadata", {}).get("published"):
			continue
		if isinstance(page_doc, dict):
			out[page] = {"blocks": blocks, "metadata": page_doc.get("metadata", {})}
	return out


def _require_management_access(company=None):
	from restaurant.api import _ensure_management_site_settings_access
	_ensure_management_site_settings_access()
	resolved = resolve_company(company)
	if resolved != "__default__":
		frappe.get_doc("Company", resolved).check_permission("read")


def _revision(value):
	return hashlib.sha256(json.dumps(value or {}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


def _check_revision(expected, current):
	if expected is not None and str(expected) != _revision(current):
		frappe.throw(_("طراحی توسط کاربر دیگری تغییر کرده است. پیش از ذخیره، نسخهٔ تازه را دریافت کنید."), frappe.TimestampMismatchError)


def _sanitize_design(value):
	if not isinstance(value, dict):
		return {}
	out = {}
	for device in ("desktop", "mobile"):
		values = value.get(device)
		if not isinstance(values, dict):
			continue
		style = {}
		for key in ("padding", "gap", "radius", "fontSize", "minHeight", "maxWidth", "columns"):
			try:
				if key in values and values[key] not in (None, ""):
					number = float(values[key])
					if math.isfinite(number):
						style[key] = max(0, min(number, 1920))
			except (TypeError, ValueError):
				pass
		for key in ("background", "color"):
			color = str(values.get(key) or "")
			if re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", color) or color in {"primary", "accent", "surface", "background", "text", "muted", "transparent"}:
				style[key] = color
		for key, allowed in {"align": {"start", "center", "end"}, "direction": {"row", "column"}}.items():
			if values.get(key) in allowed:
				style[key] = values[key]
		if "hidden" in values:
			style["hidden"] = values["hidden"] in (True, 1, "1")
		out[device] = style
	return out


@frappe.whitelist()
def get_management_page_layout(page=DEFAULT_PAGE, company=None):
	_require_management_access(company)
	resolved = resolve_company(company)
	return {
		"company": resolved,
		**get_page_layout(page, company=resolved),
	}


@frappe.whitelist()
def set_management_page_layout(payload=None, company=None):
	_require_management_access(company)

	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		framppe = frappe
		framppe.throw(_("Invalid layout payload."))

	page = _normalize_page(data.get("page"))
	blocks = _sanitize_blocks(data.get("blocks"))

	resolved = resolve_company(company)
	doc = _load_layout_doc(resolved, for_update=True)
	if not isinstance(doc, dict):
		doc = {}
	_check_revision(data.get("revision"), doc.get(page))
	if page.startswith("custom:") and page not in doc:
		frappe.throw(_("صفحه پیدا نشد؛ ابتدا صفحهٔ جدید را بسازید."))
	doc[page] = {**(doc.get(page) or {}), "blocks": blocks}
	if page.startswith("custom:") and isinstance(data.get("metadata"), dict):
		doc[page]["metadata"] = _page_metadata(data["metadata"], page)
	_save_layout_doc(resolved, doc)

	return {
		"company": resolved,
		"page": page,
		"blocks": blocks,
		"stored": True,
		"revision": _revision(doc[page]),
		"metadata": doc[page].get("metadata", {}),
	}


@frappe.whitelist()
def reset_management_page_layout(page=DEFAULT_PAGE, company=None):
	_require_management_access(company)
	page = _normalize_page(page)
	if page.startswith("custom:"):
		frappe.throw(_("برای صفحهٔ اختصاصی، بلوک‌ها را در محیط طراحی حذف کنید."))
	resolved = resolve_company(company)
	doc = _load_layout_doc(resolved, for_update=True)
	if isinstance(doc, dict) and page in doc:
		doc.pop(page, None)
		_save_layout_doc(resolved, doc)
	return {"company": resolved, "page": page, "blocks": []}


def _page_metadata(data, page):
	return {"title": str(data.get("title") or page.split(":")[-1])[:140],
		"description": str(data.get("description") or "")[:500],
		"published": data.get("published") in (True, 1, "1"),
		"slug": page.split(":", 1)[-1]}


@frappe.whitelist()
def get_management_design_library(company=None):
	_require_management_access(company)
	resolved = resolve_company(company)
	doc = _load_layout_doc(resolved)
	return {"company": resolved, "pages": [
		{"page": key, **value.get("metadata", {})}
		for key, value in doc.items() if key.startswith("custom:") and isinstance(value, dict)
	], "components": doc.get("_components", []), "revision": _revision(doc.get("_components", []))}


@frappe.whitelist()
def create_management_design_page(payload=None, company=None):
	_require_management_access(company)
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("اطلاعات صفحه معتبر نیست."))
	slug = str(data.get("slug") or "").strip().lower()
	if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", slug):
		frappe.throw(_("نشانی باید از حروف انگلیسی کوچک، عدد و خط تیره ساخته شود."))
	page = "custom:" + slug
	resolved = resolve_company(company)
	doc = _load_layout_doc(resolved, for_update=True)
	if page in doc:
		frappe.throw(_("این نشانی قبلاً برای یک صفحه استفاده شده است."))
	if sum(key.startswith("custom:") for key in doc) >= 100:
		frappe.throw(_("حداکثر صد صفحهٔ اختصاصی قابل ساخت است."))
	metadata = _page_metadata({**data, "published": False}, page)
	doc[page] = {"metadata": metadata, "blocks": _sanitize_blocks(data.get("blocks", []))}
	_save_layout_doc(resolved, doc)
	return {"company": resolved, "page": page, **doc[page], "stored": True, "revision": _revision(doc[page])}


@frappe.whitelist()
def save_management_design_component(payload=None, company=None):
	_require_management_access(company)
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("اطلاعات کامپوننت معتبر نیست."))
	resolved = resolve_company(company)
	doc = _load_layout_doc(resolved, for_update=True)
	rows = doc.get("_components", [])
	_check_revision(data.get("revision"), rows)
	block = _sanitize_block(data.get("block"), 0)
	label = str(data.get("label") or "").strip()[:100]
	if not block or not label:
		frappe.throw(_("نام و طراحی کامپوننت الزامی است."))
	if len(rows) >= 100:
		frappe.throw(_("کتابخانه حداکثر صد کامپوننت دارد."))
	component = {"id": frappe.generate_hash(length=12), "label": label, "block": block}
	doc["_components"] = [*rows, component]
	_save_layout_doc(resolved, doc)
	return {"components": doc["_components"], "revision": _revision(doc["_components"])}


@frappe.whitelist(allow_guest=True)
def get_public_design_page(slug, company=None):
	page = _normalize_page("custom:" + str(slug or ""))
	result = get_page_layout(page, company)
	if not result.get("metadata", {}).get("published"):
		frappe.throw(_("صفحه پیدا نشد."), frappe.DoesNotExistError)
	return result
