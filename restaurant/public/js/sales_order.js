frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        add_sync_work_order_button(frm);
    },
});

function add_sync_work_order_button(frm) {
    if (frm.is_new() || frm.doc.docstatus !== 1) {
        return;
    }

    frm.add_custom_button(__("Create/Sync Work Orders"), () => {
        frappe.call({
            method: "restaurant.api.sync_order_work_orders",
            args: {
                order_name: frm.doc.name,
            },
            freeze: true,
            freeze_message: __("Syncing production tickets and work orders..."),
            callback: (r) => {
                const payload = r.message || {};
                const created = payload.created_work_orders || [];
                const synced = payload.synced_work_orders || [];
                const skipped = payload.skipped_tickets || [];

                const lines = [];
                lines.push(__("Sales Order: {0}", [frm.doc.name]));
                lines.push(__("Created Work Orders: {0}", [created.length]));
                lines.push(__("Synced Work Orders: {0}", [synced.length]));
                if (skipped.length) {
                    lines.push(__("Skipped Tickets: {0}", [skipped.length]));
                }

                frappe.msgprint({
                    title: __("Production Sync"),
                    message: lines.join("<br>"),
                    indicator: skipped.length ? "orange" : "green",
                });

                frm.reload_doc();
            },
        });
    }, __("Create"));
}
