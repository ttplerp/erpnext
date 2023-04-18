// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['POS Closing Entry'] = {
	add_fields: ["payment_status"],
	get_indicator: function(doc) {
		var status_color = {
			"Deposited": "green",
			"Not Deposited": "orange",

		};
		return [__(doc.payment_status), status_color[doc.payment_status], "status,=,"+doc.payment_status];
	},
	// right_column: "grand_total"
};
