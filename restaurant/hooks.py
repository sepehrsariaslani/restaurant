app_name = "restaurant"
app_title = "Restaurant"
app_publisher = "Sepehr Sariaslani"
app_description = "This app is for managing resturants and coffee shops in Iran"
app_email = "Sepehr.sariaslani@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
#       {
#               "name": "restaurant",
#               "logo": "/assets/restaurant/logo.png",
#               "title": "Restaurant",
#               "route": "/restaurant",
#               "has_permission": "restaurant.api.permission.has_app_permission"
#       }
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/restaurant/css/restaurant.css"
app_include_js = [
        "/assets/restaurant/js/desk_print_picker.js",
        "/assets/restaurant/js/activity_tracker.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/restaurant/css/restaurant.css"
# web_include_js = "/assets/restaurant/js/restaurant.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "restaurant/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

doctype_js = {
        "Auto Price List": "public/js/auto_price_list.js",
        "Sales Order": "public/js/sales_order.js",
}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "restaurant/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
homepage = "restaurant"

# website user home page (by Role)
# role_home_page = {
#       "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

website_route_rules = [
        # Customer-facing routes (no prefix)
        {"from_route": "/table/<qr_token>", "to_route": "restaurant/menu"},
        {"from_route": "/menu", "to_route": "restaurant/menu"},
        {"from_route": "/item/<slug>", "to_route": "restaurant/item"},
        {"from_route": "/about-us", "to_route": "restaurant/about_us"},
        {"from_route": "/faq", "to_route": "restaurant/faq"},
        {"from_route": "/cart", "to_route": "restaurant/cart"},
        {"from_route": "/order-success", "to_route": "restaurant/order_success"},
        {"from_route": "/order-success/<order_code>", "to_route": "restaurant/order_success"},
        # Management routes
        {"from_route": "/management", "to_route": "management"},
        {"from_route": "/management/login", "to_route": "management/login"},
        {"from_route": "/management/dashboard", "to_route": "management"},
        {"from_route": "/management/pos", "to_route": "management/pos"},
        {"from_route": "/management/pos-profile", "to_route": "management/pos_profile"},
        {"from_route": "/management/pos_profile", "to_route": "management/pos_profile"},
        {"from_route": "/management/orders", "to_route": "management/orders"},
        {"from_route": "/management/products", "to_route": "management/products"},
        {"from_route": "/management/product", "to_route": "management/product"},
        {"from_route": "/management/menu-groups", "to_route": "management/menu_groups"},
        {"from_route": "/management/menu-group", "to_route": "management/menu_group"},
        {"from_route": "/management/site-settings", "to_route": "management/site_settings"},
        {"from_route": "/management/boms", "to_route": "management/boms"},
        {"from_route": "/management/bom", "to_route": "management/bom"},
        {"from_route": "/management/customers", "to_route": "management/customers"},
        {"from_route": "/management/reports", "to_route": "management/reports"},
        {"from_route": "/management/reports/<report_key>", "to_route": "management/report"},
        {"from_route": "/management/print-formats", "to_route": "management/print_formats"},
        {"from_route": "/management/settings", "to_route": "management/settings"},
]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#       "methods": "restaurant.utils.jinja_methods",
#       "filters": "restaurant.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "restaurant.install.before_install"
# after_install = "restaurant.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "restaurant.uninstall.before_uninstall"
# after_uninstall = "restaurant.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "restaurant.utils.before_app_install"
# after_app_install = "restaurant.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "restaurant.utils.before_app_uninstall"
# after_app_uninstall = "restaurant.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "restaurant.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#       "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#       "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#       "ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#       "*": {
#               "on_update": "method",
#               "on_cancel": "method",
#               "on_trash": "method"
#       }
# }

doc_events = {
        "BOM": {
                "on_submit": "restaurant.api.clear_item_default_bom_links_for_bom",
                "before_submit": "restaurant.api.refresh_item_nutrition_for_bom",
                "validate": "restaurant.api.refresh_item_nutrition_for_bom",
                "on_update_after_submit": "restaurant.api.clear_item_default_bom_links_for_bom",
                "on_trash": "restaurant.api.clear_item_default_bom_links_for_bom",
        },
        "Work Order": {
                "after_insert": "restaurant.api.sync_work_order_required_items_from_ticket",
                "on_update": "restaurant.api.sync_work_order_required_items_from_ticket",
                "on_cancel": "restaurant.api.unlink_work_order_from_restaurant_ticket",
                "on_trash": "restaurant.api.unlink_work_order_from_restaurant_ticket",
        },
        "Restaurant Production Ticket": {
                "on_cancel": "restaurant.api.unlink_production_ticket_links",
                "on_trash": "restaurant.api.unlink_production_ticket_links",
        },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#       "all": [
#               "restaurant.tasks.all"
#       ],
#       "daily": [
#               "restaurant.tasks.daily"
#       ],
#       "hourly": [
#               "restaurant.tasks.hourly"
#       ],
#       "weekly": [
#               "restaurant.tasks.weekly"
#       ],
#       "monthly": [
#               "restaurant.tasks.monthly"
#       ],
# }

scheduler_events = {
        "daily": [
                "restaurant.restaurant.doctype.auto_price_list.auto_price_list.run_due_restaurant_price_lists",
                "restaurant.activity_tracking.jobs.aggregate_employee_activity_daily",
                "restaurant.activity_tracking.jobs.purge_employee_activity_raw_data",
        ],
        "cron": {
                "* * * * *": [
                        "restaurant.snapp_sync.sync_snapp_orders",
                ],
                "*/5 * * * *": [
                        "restaurant.activity_tracking.jobs.close_timed_out_activity_sessions",
                ],
        }
}

# Testing
# -------

# before_tests = "restaurant.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#       "frappe.desk.doctype.event.event.get_events": "restaurant.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#       "Task": "restaurant.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["restaurant.utils.before_request"]
# after_request = ["restaurant.utils.after_request"]

on_session_creation = "restaurant.activity_tracking.api.on_session_creation"
on_logout = "restaurant.activity_tracking.api.on_logout"

# Job Events
# ----------
# before_job = ["restaurant.utils.before_job"]
# after_job = ["restaurant.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#       {
#               "doctype": "{doctype_1}",
#               "filter_by": "{filter_by}",
#               "redact_fields": ["{field_1}", "{field_2}"],
#               "partial": 1,
#       },
#       {
#               "doctype": "{doctype_2}",
#               "filter_by": "{filter_by}",
#               "partial": 1,
#       },
#       {
#               "doctype": "{doctype_3}",
#               "strict": False,
#       },
#       {
#               "doctype": "{doctype_4}"
#       }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#       "restaurant.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
#       "Logging DocType Name": 30  # days to retain logs
# }


fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "Restaurant"]],
    }
]
