// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// render
frappe.listview_settings['Prepare Audit Plan'] = {
	get_indicator: function(doc) {
		var status_color = {
			"Pending": "orange",
			"Engagement Letter": "orange",
			"Audit Execution": "orange",
			"Initial Report": "orange",
			"Follow Up": "orange",
			"Closed": "green"

		};
		return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
	},
};