"""Add order links for HRMS employee meal reservations in management POS."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CUSTOM_FIELDS = {
    "Meal Reservation": [
        {
            "fieldname": "restaurant_pos_sales_order",
            "label": "Restaurant POS Sales Order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "insert_after": "reservation_status",
            "read_only": 1,
            "no_copy": 1,
            "unique": 1,
        },
    ],
    "Sales Order": [
        {
            "fieldname": "restaurant_employee_meal_employee",
            "label": "Employee Meal Employee",
            "fieldtype": "Link",
            "options": "Employee",
            "insert_after": "restaurant_pos_client_order_key",
            "read_only": 1,
            "no_copy": 1,
        },
        {
            "fieldname": "restaurant_employee_meal_reservation",
            "label": "Employee Meal Reservation",
            "fieldtype": "Link",
            "options": "Meal Reservation",
            "insert_after": "restaurant_employee_meal_employee",
            "read_only": 1,
            "no_copy": 1,
        },
    ],
    "Sales Order Item": [
        {
            "fieldname": "restaurant_employee_meal_reservation",
            "label": "Employee Meal Reservation",
            "fieldtype": "Link",
            "options": "Meal Reservation",
            "insert_after": "restaurant_selection_summary",
            "read_only": 1,
            "no_copy": 1,
        },
    ],
}


def execute():
    if not frappe.db.exists("DocType", "Meal Reservation"):
        return
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
    frappe.clear_cache(doctype="Meal Reservation")
    frappe.clear_cache(doctype="Sales Order")
    frappe.clear_cache(doctype="Sales Order Item")
