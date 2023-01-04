// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Asset Received Entries', {
	onload: function(frm) {
		frm.set_query('branch', function(doc, cdt, cdn) {
			return {
				filters: {
					"is_disabled": 0
				}
			};
		});
	},

	refresh: function(frm) {

	}
});
