// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rental Ageing Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd":1,
			"read_only": 0,
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd":1,
			"read_only": 0,
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
		},
		{
			"fieldname": "ministry_and_agency",
			"label": __("Ministry and Agency"),
			"fieldtype": "Link",
			"options": "Ministry and Agency"
		},
		{
			"fieldname": "tenant",
			"label": __("Tenant"),
			"fieldtype": "Link",
			"options": "Tenant Information",
		}
	]
};
