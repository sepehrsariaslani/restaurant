"""Add approval and audit fields for website and Food Partner Sales Orders."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


APPROVED_STATUS = "تأیید شده"


def execute():
	if not frappe.db.exists("DocType", "Sales Order"):
		return

	create_custom_fields(
		{
			"Sales Order": [
				{
					"fieldname": "restaurant_order_review_status",
					"label": "وضعیت بررسی سفارش",
					"fieldtype": "Select",
					"options": "در انتظار بررسی\nتأیید شده\nرد شده",
					"default": APPROVED_STATUS,
					"insert_after": "restaurant_status",
					"in_list_view": 1,
					"read_only": 1,
				},
				{
					"fieldname": "restaurant_order_reviewed_by",
					"label": "بررسی‌کننده سفارش",
					"fieldtype": "Link",
					"options": "User",
					"insert_after": "restaurant_order_review_status",
					"read_only": 1,
				},
				{
					"fieldname": "restaurant_order_reviewed_at",
					"label": "زمان بررسی سفارش",
					"fieldtype": "Datetime",
					"insert_after": "restaurant_order_reviewed_by",
					"read_only": 1,
				},
				{
					"fieldname": "restaurant_order_review_note",
					"label": "یادداشت بررسی سفارش",
					"fieldtype": "Small Text",
					"insert_after": "restaurant_order_reviewed_at",
					"read_only": 1,
				},
			]
		},
		ignore_validate=True,
	)
	if frappe.db.has_column("Sales Order", "restaurant_order_review_status"):
		frappe.db.sql(
			"""
			UPDATE `tabSales Order`
			SET restaurant_order_review_status = %s
			WHERE IFNULL(restaurant_order_review_status, '') = ''
			""",
			(APPROVED_STATUS,),
		)
	frappe.clear_cache(doctype="Sales Order")
	frappe.db.commit()
