import frappe


WORKSPACE_LABEL = "Employee Activity"

SHORTCUTS = [
    {
        "type": "DocType",
        "label": "Activity Summary",
        "link_to": "Employee Activity Daily Summary",
        "doc_view": "List",
    },
    {
        "type": "DocType",
        "label": "Activity Sessions",
        "link_to": "Employee Activity Session",
        "doc_view": "List",
    },
    {
        "type": "DocType",
        "label": "Activity Settings",
        "link_to": "Employee Activity Settings",
        "doc_view": "List",
    },
]

LINKS = [
    {"type": "Card Break", "label": "Tracking"},
    {
        "type": "Link",
        "label": "Sessions",
        "link_type": "DocType",
        "link_to": "Employee Activity Session",
    },
    {
        "type": "Link",
        "label": "Slices",
        "link_type": "DocType",
        "link_to": "Employee Activity Slice",
    },
    {
        "type": "Link",
        "label": "Events",
        "link_type": "DocType",
        "link_to": "Employee Activity Event",
    },
    {
        "type": "Link",
        "label": "Daily Summary",
        "link_type": "DocType",
        "link_to": "Employee Activity Daily Summary",
    },
    {"type": "Card Break", "label": "Reports"},
    {
        "type": "Link",
        "label": "Employee Activity Overview",
        "link_type": "Report",
        "link_to": "Employee Activity Overview",
    },
    {
        "type": "Link",
        "label": "Employee Productivity Ratio",
        "link_type": "Report",
        "link_to": "Employee Productivity Ratio",
    },
    {
        "type": "Link",
        "label": "Process Bottleneck by DocType",
        "link_type": "Report",
        "link_to": "Process Bottleneck by DocType",
    },
]


REQUIRED_DOCTYPES = {
    "Employee Activity Settings",
    "Employee Activity Session",
    "Employee Activity Slice",
    "Employee Activity Event",
    "Employee Activity Daily Summary",
}

REQUIRED_REPORTS = {
    "Employee Activity Overview",
    "Employee Productivity Ratio",
    "Process Bottleneck by DocType",
}


def _has_field(doc, fieldname):
    return doc.meta.has_field(fieldname)


def _set_if_field(doc, fieldname, value):
    if _has_field(doc, fieldname):
        doc.set(fieldname, value)


def execute():
    if not frappe.db.exists("DocType", "Workspace"):
        return

    missing_doctypes = [dt for dt in REQUIRED_DOCTYPES if not frappe.db.exists("DocType", dt)]
    if missing_doctypes:
        frappe.throw("Missing employee activity doctypes: " + ", ".join(sorted(missing_doctypes)))

    missing_reports = [report for report in REQUIRED_REPORTS if not frappe.db.exists("Report", report)]
    if missing_reports:
        frappe.throw("Missing employee activity reports: " + ", ".join(sorted(missing_reports)))

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
    _set_if_field(doc, "icon", "analytics")
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
        doc.append("roles", {"role": "HR Manager"})

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    frappe.clear_cache()
