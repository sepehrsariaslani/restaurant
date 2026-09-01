import frappe


DOCTYPE_NAME = "Restaurant POS Offline Mutation"


def execute():
    if frappe.db.exists("DocType", DOCTYPE_NAME):
        return

    frappe.get_doc(
        {
            "doctype": "DocType",
            "name": DOCTYPE_NAME,
            "module": "Restaurant",
            "custom": 1,
            "istable": 0,
            "editable_grid": 0,
            "track_changes": 0,
            "fields": [
                {
                    "fieldname": "client_mutation_key",
                    "label": "POS Client Mutation Key",
                    "fieldtype": "Data",
                    "reqd": 1,
                    "unique": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "mutation_type",
                    "label": "Mutation Type",
                    "fieldtype": "Data",
                    "reqd": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "status",
                    "label": "Status",
                    "fieldtype": "Select",
                    "options": "created\nneeds_attention",
                    "default": "created",
                    "reqd": 1,
                    "in_list_view": 1,
                },
                {
                    "fieldname": "result_json",
                    "label": "Replay Result",
                    "fieldtype": "Long Text",
                    "read_only": 1,
                },
            ],
        }
    ).insert(ignore_permissions=True)
    frappe.clear_cache(doctype=DOCTYPE_NAME)
