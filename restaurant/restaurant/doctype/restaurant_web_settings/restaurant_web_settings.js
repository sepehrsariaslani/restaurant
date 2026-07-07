frappe.ui.form.on("Restaurant Web Settings", {
    refresh(frm) {
        frm.add_custom_button(__("Sync New Snapp Orders"), () => {
            frappe.call({
                method: "restaurant.api.run_snapp_sync_now",
                args: {
                    only_new: 1,
                },
                freeze: true,
                freeze_message: __("Syncing new Snapp orders..."),
                callback: (response) => {
                    const payload = response.message || {};
                    if (payload.status !== "success") {
                        frappe.msgprint({
                            title: __("Sync Failed"),
                            message: __(payload.reason || "Snapp sync failed."),
                            indicator: "red",
                        });
                        return;
                    }

                    frappe.msgprint({
                        title: __("Snapp Sync Completed"),
                        indicator: "green",
                        message: __(
                            "Created: {0}<br>Skipped(existing): {1}<br>Failed: {2}<br>Fetched: {3}",
                            [
                                payload.created_count || 0,
                                payload.skipped_count || 0,
                                payload.failed_count || 0,
                                payload.fetched_count || 0,
                            ],
                        ),
                    });
                    frm.reload_doc();
                },
            });
        });

        frm.add_custom_button(__("Organize Imported Items"), () => {
            frappe.call({
                method: "restaurant.api.organize_catalog_items",
                args: {
                    enable_for_menu: 1,
                },
                freeze: true,
                freeze_message: __("Organizing imported items..."),
                callback: (response) => {
                    const payload = response.message || {};
                    if (payload.status !== "success") {
                        frappe.msgprint({
                            title: __("Catalog Update Failed"),
                            message: __("Could not organize imported items."),
                            indicator: "red",
                        });
                        return;
                    }

                    frappe.msgprint({
                        title: __("Catalog Updated"),
                        indicator: "green",
                        message: __("Updated items: {0}", [payload.items_updated || 0]),
                    });
                    frm.reload_doc();
                },
            });
        });

        frm.add_custom_button(__("Repair Existing Snapp Orders"), () => {
            frappe.call({
                method: "restaurant.api.run_snapp_repair_orders",
                args: {
                    batch_size: 200,
                },
                freeze: true,
                freeze_message: __("Repairing imported Snapp orders and amounts..."),
                callback: (response) => {
                    const payload = response.message || {};
                    if (payload.status !== "success") {
                        frappe.msgprint({
                            title: __("Repair Failed"),
                            message: __("Could not repair existing Snapp orders."),
                            indicator: "red",
                        });
                        return;
                    }

                    frappe.msgprint({
                        title: __("Repair Completed"),
                        indicator: "green",
                        message: __(
                            "Updated: {0}<br>Failed: {1}<br>Multiplier: {2}",
                            [
                                payload.orders_updated || 0,
                                payload.orders_failed || 0,
                                payload.multiplier || 1,
                            ],
                        ),
                    });
                    frm.reload_doc();
                },
            });
        });
    },
});
