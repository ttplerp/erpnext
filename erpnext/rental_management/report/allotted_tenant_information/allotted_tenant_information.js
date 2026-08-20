// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Allotted Tenant Information"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			// default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			// default: frappe.datetime.get_today(),
		},
		{
			"fieldname": "ministry_agency",
			"label": __("Ministry/Agency"),
			"fieldtype": "Link",
			"options": "Ministry and Agency"
		},
		{
			"fieldname": "dzongkhag",
			"label": __("Dzongkhag"),
			"fieldtype": "Link",
			"options": "Dzongkhag"
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Locations"
		},
		{
			"fieldname": "building_classification",
			"label": __("Building Classification"),
			"fieldtype": "Link",
			"options": "Building Classification"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["", "Allocated", "Surrendered"],
			default: "Allocated"
		},
		{
			"fieldname": "flat_no",
			"label": __("Flat No"),
			"fieldtype": "Link",
			options: "Flat No"
		},
		{
			"fieldname": "old_flat_no",
			"label": __("Old Flat No"),
			"fieldtype": "Data",
		},
	]
};
