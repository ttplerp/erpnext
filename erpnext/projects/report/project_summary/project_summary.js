// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Project Summary"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
		},
		{
			"fieldname": "name",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project",
		},
		// {
		// 	"fieldname": "is_active",
		// 	"label": __("Is Active"),
		// 	"fieldtype": "Select",
		// 	"options": "\nYes\nNo",
		// 	"default": "Yes",
		// },
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nOpen\nCompleted",
			"default": "Open"
		},
		{
			"fieldname": "project_type",
			"label": __("Project Type"),
			"fieldtype": "Link",
			"options": "Project Type"
		},
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.id == "net_profit") {
			if (data["net_profit"] > 0) {
				value = `<p style="color: green; font-weight: bold">${value}</p>`;
			} else if (data["net_profit"] < 0) {
				value = `<p style="color: red; font-weight: bold">${value}</p>`;
			} else {
				value = `<p style="color: gray; font-weight: normal">${value}</p>`;
			}
		}
		return value;
	}
};
