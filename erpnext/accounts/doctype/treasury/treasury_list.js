// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings['Treasury'] = {
	get_indicator: function(doc) {
		var status_color = {
			"Active": "green",
			"Renewed": "orange",
			"Closed": "red"

		};
		return [__(doc.status), status_color[doc.status], "status,=," + doc.status];
	},
};
