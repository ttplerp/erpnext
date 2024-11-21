// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Daily Work Report"] = {
	"filters": [
		{
			"fieldname": "report_type",
			"label": __("Report Type"),
			"fieldtype": "Select",
			"options": "\nLabour Cost Details\nMachinery and Equipment\nMaterial Consumption\nExpenditure of Project Implementation Unit\nExpenditure for Mess\nHSD Issued Details",
			"reqd": 1
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			"fieldname": "mr_type",
			"label": __("MR Type"),
			"fieldtype": "Link",
			"options": "Muster Roll Type",
			"depends_on": "eval:doc.report_type == 'Labour Cost Details'"
		},
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
			default: frappe.datetime.nowdate(),
			"reqd": 1,
		},
	]
};
