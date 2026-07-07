frappe.provide('restaurant.auto_price_list');

frappe.ui.form.on('Auto Price List', {
    refresh: function (frm) {
        if (frm.doc.restaurant_mode) {
            apply_restaurant_mode_ui(frm);
            add_restaurant_run_now_button(frm);
        }

        // دکمه اعمال قیمت‌ها - برای هر دو حالت (قبل و بعد از Submit)
        if (frm.fields_dict.update_prices_button && frm.fields_dict.update_prices_button.$input) {
            frm.fields_dict.update_prices_button.$input.off('click.pricing').on('click.pricing', function () {
                frappe.confirm(
                    'آیا می‌خواهید قیمت‌های این لیست را در لیست قیمت "' + frm.doc.price_list + '" اعمال کنید؟',
                    function () {
                        frappe.call({
                            method: 'restaurant.restaurant.doctype.auto_price_list.auto_price_list.update_prices',
                            args: {
                                docname: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __('در حال اعمال قیمت‌ها...'),
                            callback: function (r) {
                                if (r.message && r.message.success) {
                                    frappe.show_alert({
                                        message: r.message.message,
                                        indicator: r.message.indicator
                                    });
                                } else if (r.message) {
                                    frappe.msgprint({
                                        title: 'خطا',
                                        message: r.message.message,
                                        indicator: 'red'
                                    });
                                }
                            }
                        });
                    }
                );
            });
        }

        // مخفی کردن تب‌های فرآیندها و عملیات‌ها بعد از Submit
        if (frm.doc.docstatus === 1) {
            frm.set_df_property('pricing_strategies_tab', 'hidden', 1);
            frm.set_df_property('pricing_processes_tab', 'hidden', 1);
            frm.set_df_property('bulk_pricing_tab', 'hidden', 1);
        }
    }
    // Removed auto-triggers: profit_margin, items_add, items_remove
    // These were calling calculate_prices() on every change, which called
    // update_item_prices_with_details + frm.reload_doc(), overwriting unsaved changes.
    // Use the manual "محاسبه بهای تمام شده" button instead.
});

function apply_restaurant_mode_ui(frm) {
    const tabs_to_hide = [
        'pricing_strategies_tab',
        'reports_tab'
    ];
    tabs_to_hide.forEach((fieldname) => {
        if (frm.fields_dict[fieldname]) {
            frm.set_df_property(fieldname, 'hidden', 1);
        }
    });

    const fields_to_hide = [
        'enable_installment',
        'enable_deferred_payment',
        'commission_percentage'
    ];
    fields_to_hide.forEach((fieldname) => {
        if (frm.fields_dict[fieldname]) {
            frm.set_df_property(fieldname, 'hidden', 1);
        }
    });
}

function add_restaurant_run_now_button(frm) {
    if (frm.is_new() || frm.doc.__islocal) {
        return;
    }

    frm.add_custom_button(__('Run Restaurant Pricing'), function () {
        frappe.call({
            method: 'restaurant.restaurant.doctype.auto_price_list.auto_price_list.run_restaurant_pricing',
            args: {
                docname: frm.doc.name,
                apply_prices: 1
            },
            freeze: true,
            freeze_message: __('در حال اجرای قیمت‌گذاری رستوران...'),
            callback: function (r) {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: r.message.message || __('اجرای قیمت‌گذاری انجام شد'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                    return;
                }

                frappe.msgprint({
                    title: __('خطا'),
                    message: (r.message && r.message.message) || __('اجرا با خطا مواجه شد'),
                    indicator: 'red'
                });
            }
        });
    }, __('Restaurant Pricing'));
}
