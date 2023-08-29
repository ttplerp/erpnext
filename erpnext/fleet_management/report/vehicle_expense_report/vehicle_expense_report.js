// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Vehicle Expense Report"] = {
	"filters": [
		{
			"fieldname": "equipment",
			"fieldtype": "Link",
			"label": __("Equipment"),
			"options": "Equipment",
			"reqd": 0
		},
		{
			"fieldname": "type",
			"fieldtype": "Select",
			"label": __("Type"),
			"options": "\nPOL Receive\nPOL Issue\nBluebook\nEmission\nFitness"
		},
		{
			"fieldname": "consolidate",
			"fieldtype": "Check",
			"label": __("Consolidate"),
			"default": 0,
			"reqd": 0
		},
		{
			"fieldname": "from_date",
			"label": ("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": "",
		},
		{
			"fieldname": "to_date",
			"label": ("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": "",
		},
	]
};
