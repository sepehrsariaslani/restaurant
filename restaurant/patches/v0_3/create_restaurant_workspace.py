import frappe


WORKSPACE_LABEL = "رستوران"

SHORTCUTS = [
    {"type": "DocType", "label": "میزها", "link_to": "Restaurant Table", "doc_view": "List"},
    {"type": "DocType", "label": "سشن میز", "link_to": "Restaurant Table Session", "doc_view": "List"},
    {"type": "DocType", "label": "سفارش میز", "link_to": "Restaurant Table Order", "doc_view": "List"},
    {"type": "DocType", "label": "درخواست میز", "link_to": "Restaurant Table Request", "doc_view": "List"},
    {"type": "DocType", "label": "آیتم‌های منو", "link_to": "Restaurant Table Menu Item", "doc_view": "List"},
]

LINKS = [
    {"type": "Card Break", "label": "عملیات سالن"},
    {
        "type": "Link",
        "label": "میزها",
        "link_type": "DocType",
        "link_to": "Restaurant Table",
    },
    {
        "type": "Link",
        "label": "سشن‌های میز",
        "link_type": "DocType",
        "link_to": "Restaurant Table Session",
    },
    {
        "type": "Link",
        "label": "درخواست‌های میز",
        "link_type": "DocType",
        "link_to": "Restaurant Table Request",
    },
    {"type": "Card Break", "label": "سفارش و منو"},
    {
        "type": "Link",
        "label": "سفارش‌های میز",
        "link_type": "DocType",
        "link_to": "Restaurant Table Order",
    },
    {
        "type": "Link",
        "label": "آیتم سفارش میز",
        "link_type": "DocType",
        "link_to": "Restaurant Table Order Item",
    },
    {
        "type": "Link",
        "label": "آیتم‌های منوی میز",
        "link_type": "DocType",
        "link_to": "Restaurant Table Menu Item",
    },
    {"type": "Card Break", "label": "ERPNext"},
    {
        "type": "Link",
        "label": "آیتم ERPNext",
        "link_type": "DocType",
        "link_to": "Item",
    },
    {
        "type": "Link",
        "label": "Sales Order",
        "link_type": "DocType",
        "link_to": "Sales Order",
    },
]

REQUIRED_DOCTYPES = {
    "Restaurant Table",
    "Restaurant Table Session",
    "Restaurant Table Menu Item",
    "Restaurant Table Order",
    "Restaurant Table Order Item",
    "Restaurant Table Request",
}



def _has_field(doc, fieldname):
    return doc.meta.has_field(fieldname)



def _set_if_field(doc, fieldname, value):
    if _has_field(doc, fieldname):
        doc.set(fieldname, value)



def execute():
    if not frappe.db.exists("DocType", "Workspace"):
        return

    missing = [dt for dt in REQUIRED_DOCTYPES if not frappe.db.exists("DocType", dt)]
    if missing:
        frappe.throw("Missing required DocTypes for restaurant workspace: " + ", ".join(sorted(missing)))

    workspace_name = frappe.db.get_value("Workspace", {"label": WORKSPACE_LABEL}, "name")
    if not workspace_name and frappe.db.exists("Workspace", WORKSPACE_LABEL):
        workspace_name = WORKSPACE_LABEL

    if workspace_name:
        doc = frappe.get_doc("Workspace", workspace_name)
    else:
        doc = frappe.new_doc("Workspace")
        doc.label = WORKSPACE_LABEL

    _set_if_field(doc, "title", WORKSPACE_LABEL)
    _set_if_field(doc, "module", "Restaurant")
    _set_if_field(doc, "icon", "small-file")
    _set_if_field(doc, "public", 1)
    _set_if_field(doc, "is_hidden", 0)
    _set_if_field(doc, "hide_custom", 0)
    _set_if_field(doc, "parent_page", "")
    _set_if_field(doc, "content", "[]")

    if _has_field(doc, "shortcuts"):
        doc.set("shortcuts", [])
        for row in SHORTCUTS:
            doc.append("shortcuts", row)

    if _has_field(doc, "links"):
        doc.set("links", [])
        for row in LINKS:
            doc.append("links", row)

    if _has_field(doc, "roles"):
        doc.set("roles", [])
        doc.append("roles", {"role": "System Manager"})
        doc.append("roles", {"role": "Desk User"})

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    frappe.clear_cache()
