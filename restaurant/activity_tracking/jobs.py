import frappe

from restaurant.activity_tracking import service


def close_timed_out_activity_sessions():
    closed = service.close_timed_out_sessions()
    if closed:
        frappe.logger().info("Employee activity: closed %s timed out sessions", closed)


def aggregate_employee_activity_daily():
    written = service.aggregate_daily_activity()
    frappe.logger().info("Employee activity: daily summary rows upserted=%s", written)


def purge_employee_activity_raw_data():
    purge_info = service.purge_raw_activity()
    frappe.logger().info("Employee activity: purge completed %s", purge_info)
