import frappe
import json

frappe.init(site="restaurant")
frappe.connect()

from restaurant.api import get_kitchen_display_orders
try:
    orders = get_kitchen_display_orders(limit=2)
    print("API Output Keys:", orders.keys())
    print("Orders list length:", len(orders.get("orders", [])))
except Exception as e:
    print("Error:", e)
