// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Utility Service Type', {
	setup: function(frm) {
		frm.set_query("account", "accounts", function(doc, cdt, cdn) {
			let child = locals[cdt][cdn];
			return {
				filters: {
					"is_group": 0,
					"company": child.company
				}
			};
		});
	},

	refresh: function(frm) {

	}
});
