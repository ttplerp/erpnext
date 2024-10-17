// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Foreign Exchange', {
	// refresh: function(frm) {

	// }
	currency: (frm) => {
        let company_currency = erpnext.get_currency(frm.doc.company);
		if (company_currency != frm.doc.company) {
			frappe.call({
				method: "erpnext.setup.utils.get_exchange_rate",
				args: {
					from_currency: company_currency,
					to_currency: frm.doc.currency,
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("exchange_rate", flt(r.message));
						frm.set_df_property(
							"exchange_rate",
							"description",
							"1 " + frm.doc.currency + " = [?] " + company_currency
						);
					}
				},
			});
		} else {
			frm.set_value("exchange_rate", 1.0);
			frm.set_df_property("exchange_rate", "hidden", 1);
			frm.set_df_property("exchange_rate", "description", "");
		}

		frm.trigger("amount");
		frm.trigger("set_dynamic_field_label");
	},

	amount: (frm) => {
        frm.set_value("base_amount", flt(frm.doc.amount) * flt(frm.doc.exchange_rate));
    },

	set_dynamic_field_label: function (frm) {
		// frm.trigger("change_grid_labels");
		frm.trigger("change_form_labels");
	},

	change_form_labels: function (frm) {
		let company_currency = erpnext.get_currency(frm.doc.company);
		frm.set_currency_labels(["base_amount"], company_currency);
		frm.set_currency_labels(["amount"], frm.doc.currency);

		// toggle fields
		frm.toggle_display(
			["exchange_rate", "base_amount"],
			frm.doc.currency != company_currency
		);
	},

    change_grid_labels: function (frm) {
		let company_currency = erpnext.get_currency(frm.doc.company);
		frm.set_currency_labels(["base_amount"], company_currency, "items");
		frm.set_currency_labels(["amount"], frm.doc.currency, "items");

		let item_grid = frm.fields_dict.items.grid;
		$.each(["base_amount"], function (i, fname) {
			if (frappe.meta.get_docfield(item_grid.doctype, fname))
				item_grid.set_column_disp(fname, frm.doc.currency != company_currency);
		});
		frm.refresh_fields();
	},
});
