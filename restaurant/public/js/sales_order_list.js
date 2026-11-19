(function () {
	frappe.listview_settings = frappe.listview_settings || {};

	const salesOrderListSettings = frappe.listview_settings["Sales Order"] || {};
	const originalSalesOrderIndicator = salesOrderListSettings.get_indicator;

	salesOrderListSettings.add_fields = [
		...new Set([...(salesOrderListSettings.add_fields || []), "restaurant_status"]),
	];

	salesOrderListSettings.get_indicator = function (doc) {
		if (["cancelled", "canceled"].includes(String(doc.restaurant_status || "").trim().toLowerCase())) {
			return [__("لغوشده"), "red", "restaurant_status,=,cancelled"];
		}
		return originalSalesOrderIndicator ? originalSalesOrderIndicator.call(this, doc) : undefined;
	};

	frappe.listview_settings["Sales Order"] = salesOrderListSettings;

	if (!document.getElementById("foodpartner-cancelled-sales-order-row-style")) {
		const style = document.createElement("style");
		style.id = "foodpartner-cancelled-sales-order-row-style";
		style.textContent = `
			.list-row-container:has([data-filter="restaurant_status,=,cancelled"]) .list-row {
				background-color: rgba(239, 68, 68, 0.08);
			}
			.list-row-container:has([data-filter="restaurant_status,=,cancelled"]) .list-row:hover {
				background-color: rgba(239, 68, 68, 0.14);
			}
		`;
		document.head.appendChild(style);
	}
})();
