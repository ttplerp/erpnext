// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Court Case Tracking Report"] = {
	"filters": [
		// {
		// 	"fieldname": "enote_type",
		// 	"label": __("eNote Type"),
		// 	"fieldtype": "Link",
		// 	"options": "eNote Type"
		// },
		{
			"fieldname": "case_type",
			"label": __("Case Type"),
			"fieldtype": "Select",
			"options": "\nNPL Recovery Cases\nCounter Litigation\nCriminal & ACC Cases"
		},
	]
};
