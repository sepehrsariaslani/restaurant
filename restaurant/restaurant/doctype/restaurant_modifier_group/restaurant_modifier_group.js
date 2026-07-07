frappe.ui.form.on("Restaurant Modifier Option", {
	option_item(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row || row.action_type !== "add_on" || !row.option_item) {
			return;
		}

		frappe.db.get_value("Item", row.option_item, ["stock_uom", "valuation_rate", "standard_rate"]).then((r) => {
			const data = r.message || {};
			const rate = flt(data.valuation_rate || data.standard_rate || 0);
			frappe.model.set_value(cdt, cdn, "option_uom", data.stock_uom || "");
			frappe.model.set_value(cdt, cdn, "option_cost_rate", rate);

			const qty = flt(row.option_qty || 1);
			frappe.model.set_value(cdt, cdn, "option_cost_amount", qty * rate);
		});
	},

	action_type(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row) {
			return;
		}

		if (row.action_type === "bom_variant") {
			frappe.model.set_value(cdt, cdn, "option_item", "");
			frappe.model.set_value(cdt, cdn, "option_uom", "");
			frappe.model.set_value(cdt, cdn, "option_cost_rate", 0);
			frappe.model.set_value(cdt, cdn, "option_cost_amount", 0);
			frappe.model.set_value(cdt, cdn, "option_qty", 1);
			frappe.model.set_value(cdt, cdn, "min_qty", 1);
			frappe.model.set_value(cdt, cdn, "max_qty", 1);
			frappe.model.set_value(cdt, cdn, "qty_step", 1);
		}
	},

	option_qty(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row) {
			return;
		}
		const qty = Math.max(flt(row.option_qty || 1), 0);
		const rate = Math.max(flt(row.option_cost_rate || 0), 0);
		frappe.model.set_value(cdt, cdn, "option_cost_amount", qty * rate);
	},

	option_cost_rate(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (!row) {
			return;
		}
		const qty = Math.max(flt(row.option_qty || 1), 0);
		const rate = Math.max(flt(row.option_cost_rate || 0), 0);
		frappe.model.set_value(cdt, cdn, "option_cost_amount", qty * rate);
	},
});
