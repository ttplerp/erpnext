frappe.listview_settings['Vehicle Request'] = {
	get_indicator: function(doc) {
		var indicator = [__(doc.status), frappe.utils.guess_colour(doc.status), "status,=," + doc.status];
		indicator[1] = {"Closed": "green", "Booked":"orange"}[doc.status];
		return indicator;
	}
};