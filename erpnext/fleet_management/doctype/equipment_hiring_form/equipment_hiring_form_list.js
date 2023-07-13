frappe.listview_settings['Equipment Hiring Form'] = {
	get_indicator: function(doc) {
		return [__(doc.status), {
			"Hiring Requested": "red",
			"Hiring Approved": "blue",
			"Closed": "green",
			"Cancelled": "red",
			"Logbook Submitted": "orange",
		}[doc.status], "status,=," + doc.status];
	}
};