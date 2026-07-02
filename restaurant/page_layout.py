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

import frappe
from frappe import _

PAGE_LAYOUT_KEY_PREFIX = "restaurant_page_layout_v1"
SUPPORTED_PAGES = {"home"}
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
	return value if value in SUPPORTED_PAGES else DEFAULT_PAGE


def _load_layout_doc(company):
	"""Return the full {page: {blocks: [...]}} map for a company."""
	try:
		raw = frappe.defaults.get_global_default(_storage_key(company))
	except Exception:
		raw = None
	parsed = _parse_json(raw, {})
	return parsed if isinstance(parsed, dict) else {}


def _save_layout_doc(company, doc):
	key = _storage_key(company)
	frame = json.dumps(doc, ensure_ascii=False)
	frame = frame[:900000]  # hard cap so a global default cannot be abused
	framppe_set_global_default(key, frame)


def framppe_set_global_default(key, value):
	# Small indirection so tests can patch it; Frappe API name kept intact.
	framppe = frappe
	framppe.db.set_global(key, value)


def _sanitize_block(raw, index):
	if not isinstance(raw, dict):
		return None
	block_type = str(raw.get("type") or "").strip()
	if block_type not in ALLOWED_BLOCK_TYPES:
		return None

	props = raw.get("props")
	if not isinstance(props, dict):
		props = {}

	return {
		"id": str(raw.get("id") or f"{block_type}_{index}").strip() or f"{block_type}_{index}",
		"type": block_type,
		"variant": str(raw.get("variant") or "").strip(),
		"enabled": 0 if str(raw.get("enabled")) in ("0", "false", "False") else 1,
		"order": index,
		"props": props,
	}


def _sanitize_blocks(blocks):
	if not isinstance(blocks, list):
		return []
	out = []
	for index, raw in enumerate(blocks[:MAX_BLOCKS_PER_PAGE]):
		block = _sanitize_block(raw, index)
		if block:
			out.append(block)
	return out


def get_page_layout(page=DEFAULT_PAGE, company=None):
	"""Internal read used by the public boot. Never raises."""
	page = _normalize_page(page)
	doc = _load_layout_doc(company)
	page_doc = doc.get(page) if isinstance(doc, dict) else None
	blocks = _sanitize_blocks((page_doc or {}).get("blocks")) if isinstance(page_doc, dict) else []
	return {"page": page, "blocks": blocks}


def get_boot_page_layout(company=None):
	"""Return the {page: {blocks}} map for injection into boot.

	Only includes pages that actually have stored blocks, so the frontend
	fallback (buildLegacyLayout) still kicks in for undesigned pages.
	"""
	out = {}
	for page in SUPPORTED_PAGES:
		layout = get_page_layout(page, company=company)
		if layout.get("blocks"):
			out[page] = {"blocks": layout["blocks"]}
	return out


def _require_management_access():
	if frappe.session.user == "Guest":
		framppe = frappe
		framppe.throw(_("You must be logged in."), frappe.PermissionError)


@frappe.whitelist()
def get_management_page_layout(page=DEFAULT_PAGE, company=None):
	_require_management_access()
	resolved = resolve_company(company)
	return {
		"company": resolved,
		**get_page_layout(page, company=resolved),
	}


@frappe.whitelist()
def set_management_page_layout(payload=None, company=None):
	_require_management_access()

	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		framppe = frappe
		framppe.throw(_("Invalid layout payload."))

	page = _normalize_page(data.get("page"))
	blocks = _sanitize_blocks(data.get("blocks"))

	resolved = resolve_company(company)
	doc = _load_layout_doc(resolved)
	if not isinstance(doc, dict):
		doc = {}
	doc[page] = {"blocks": blocks}
	_save_layout_doc(resolved, doc)

	return {
		"company": resolved,
		"page": page,
		"blocks": blocks,
	}


@frappe.whitelist()
def reset_management_page_layout(page=DEFAULT_PAGE, company=None):
	_require_management_access()
	page = _normalize_page(page)
	resolved = resolve_company(company)
	doc = _load_layout_doc(resolved)
	if isinstance(doc, dict) and page in doc:
		doc.pop(page, None)
		_save_layout_doc(resolved, doc)
	return {"company": resolved, "page": page, "blocks": []}
