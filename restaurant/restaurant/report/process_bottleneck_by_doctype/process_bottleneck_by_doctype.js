frappe.query_reports["Process Bottleneck by DocType"] = {
    filters: [
        {
            fieldname: "date_from",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
            reqd: 1,
        },
        {
            fieldname: "date_to",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1,
        },
        {
            fieldname: "user",
            label: __("User"),
            fieldtype: "Link",
            options: "User",
        },
    ],
};
