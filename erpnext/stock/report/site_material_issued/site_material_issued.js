// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Site Material Issued"] = {
	"filters": [
		{
			"fieldname": "entry_type",
			"label": __("Entry Type"),
			"fieldtype": "Select",
			"options": ["Material Issue", "Material Transfer"],
			"default": "Material Issue"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default":frappe.datetime.year_start(),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.get_today(),
			"redq": 1
		},
		{
			"fieldname": "rental_type",
			"label": __("Rental Site"),
			"fieldtype": "Select",
			"options": ["", "Flat No", "Location", "Block No", "Locations"]
		},
		{
			"fieldname":"site_name",
			"label": __("Site"),
			"fieldtype": "Dynamic Link",
			"get_options": function() {
				var rental_type = frappe.query_report.get_filter_value('rental_type');
				var site_name = frappe.query_report.get_filter_value('site_name');
				if(site_name && !rental_type) {
					frappe.throw(__("Please select Rentasl Type first"));
				}
				return rental_type;
			}
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},

	]
};
