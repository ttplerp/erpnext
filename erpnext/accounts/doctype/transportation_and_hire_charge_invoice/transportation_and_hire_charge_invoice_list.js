frappe.listview_settings['Transportation and Hire Charge Invoice'] = {
	add_fields: ["status"],
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		const status_colors = {
			"Unpaid": "orange",
			"Paid": "green",
			"Cancelled": "red",
			"Draft": "red",
			"Partly Paid": "yellow",
		};

		if (status_colors[doc.status]) {
			return [
				__(doc.status),
				status_colors[doc.status],
				"status,=," + doc.status,
			];
		}
	}
};