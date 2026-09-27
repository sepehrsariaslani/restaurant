import json

import frappe
from frappe import _
from frappe.utils import cint
from frappe.utils.html_utils import sanitize_html

DOCTYPE = "Restaurant Blog Post"


def _clean_post(doc, include_body=False):
    result = {
        "name": doc.name,
        "title": doc.title,
        "route": doc.route,
        "category": doc.category,
        "excerpt": doc.excerpt,
        "cover_image": doc.cover_image,
        "is_published": cint(doc.is_published),
        "is_featured": cint(doc.is_featured),
        "published_on": str(doc.published_on) if doc.published_on else None,
        "read_time": cint(doc.read_time) or 1,
        "meta_title": doc.meta_title,
        "meta_description": doc.meta_description,
        "related_products": [],
    }
    if include_body:
        result["body_html"] = sanitize_html(doc.body_html or "")
    for row in doc.related_products or []:
        item = frappe.db.get_value("Item", row.item_code, ["item_name", "restaurant_slug", "image", "disabled"], as_dict=True)
        if not item or item.disabled:
            continue
        result["related_products"].append({
            "item_code": row.item_code,
            "title": row.custom_label or item.item_name or row.item_code,
            "custom_label": row.custom_label,
            "item_name": item.item_name,
            "note": row.note,
            "image": row.image_override or item.image,
            "url": "/item/" + (item.restaurant_slug or frappe.scrub(row.item_code)),
        })
    return result


@frappe.whitelist(allow_guest=True)
def get_public_blog_posts(limit=12, category=None):
    limit = max(1, min(cint(limit) or 12, 48))
    filters = {"is_published": 1}
    if category:
        filters["category"] = category
    docs = frappe.get_all(DOCTYPE, filters=filters, fields=["name"], order_by="published_on desc, modified desc", limit_page_length=limit)
    return {"posts": [_clean_post(frappe.get_doc(DOCTYPE, row.name)) for row in docs], "categories": get_public_blog_categories()}


@frappe.whitelist(allow_guest=True)
def get_public_blog_post(route):
    doc = frappe.db.get_value(DOCTYPE, {"route": route, "is_published": 1}, "name")
    if not doc:
        frappe.throw(_("مقاله پیدا نشد."), frappe.DoesNotExistError)
    return {"post": _clean_post(frappe.get_doc(DOCTYPE, doc), include_body=True)}


@frappe.whitelist(allow_guest=True)
def get_public_blog_categories():
    return frappe.get_all(DOCTYPE, filters={"is_published": 1, "category": ["is", "set"]}, fields=["category"], group_by="category", order_by="category asc", pluck="category")


def _guard():
    from restaurant.api import _ensure_management_access
    _ensure_management_access()


@frappe.whitelist()
def get_management_blog_posts(search=None):
    _guard()
    filters = {}
    if search:
        filters["title"] = ["like", f"%{search}%"]
    rows = frappe.get_all(DOCTYPE, filters=filters, fields=["name"], order_by="modified desc", limit_page_length=200)
    return [_clean_post(frappe.get_doc(DOCTYPE, row.name)) for row in rows]


@frappe.whitelist()
def get_management_blog_post(name):
    _guard()
    return _clean_post(frappe.get_doc(DOCTYPE, name), include_body=True)


@frappe.whitelist()
def save_management_blog_post(payload):
    _guard()
    if isinstance(payload, str):
        payload = json.loads(payload)
    payload = payload or {}
    doc = frappe.get_doc(DOCTYPE, payload.get("name")) if payload.get("name") else frappe.new_doc(DOCTYPE)
    for key in ("title", "route", "category", "excerpt", "cover_image", "body_html", "is_published", "is_featured", "read_time", "meta_title", "meta_description"):
        if key in payload:
            setattr(doc, key, payload[key])
    doc.set("related_products", [])
    for row in payload.get("related_products") or []:
        if row.get("item_code"):
            doc.append("related_products", {key: row.get(key) for key in ("item_code", "custom_label", "note", "image_override")})
    doc.save()
    frappe.db.commit()
    return _clean_post(doc, include_body=True)


@frappe.whitelist()
def delete_management_blog_post(name):
    _guard()
    frappe.delete_doc(DOCTYPE, name)
    frappe.db.commit()
    return {"ok": True}


@frappe.whitelist()
def search_management_blog_products(query=""):
    _guard()
    query = (query or "").strip()
    if not query:
        return []
    return frappe.get_all("Item", filters={"disabled": 0, "item_name": ["like", f"%{query}%"]}, fields=["name as item_code", "item_name", "image"], limit_page_length=20, order_by="item_name asc")
