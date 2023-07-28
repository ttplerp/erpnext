// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Key Indicators Report"] = {
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
			"fieldname": "current_from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "current_to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "include_default_book_entries",
			"label": __("Include Default Book Entries"),
			"fieldtype": "Check",
			"default": 1,
		},
		{
			"fieldname": "comparison_from_date",
			"label": __("Comparison From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "comparison_to_date",
			"label": __("Comparison To Date"),
			"fieldtype": "Date",
			"reqd": 1
		}
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname.includes('actual')) {

			if (data[column.fieldname] < 0) {
				value = "<span style='color:red'>" + value + "</span>";
			}
			else if (data[column.fieldname] > 0) {
				value = "<span style='color:green'>" + value + "</span>";
			}
		}
		if (column.fieldname.includes('planned')) {

			if (data[column.fieldname] < 0) {
				value = "<span style='color:red'>" + value + "</span>";
			}
			else if (data[column.fieldname] > 0) {
				value = "<span style='color:green'>" + value + "</span>";
			}
		}
		if (data.account == "Key Indicators" && column.id == "account") {
			value = "<span style='color:black!important; font-weight:bold'; font-style: italic !important;'>" + value + "</span>";
		}
		if (data.account == "Headcount" && column.id == "account") {
			value = "<span style='color:black!important; font-weight:bold'; font-style: italic !important;'>" + value + "</span>";
		}
		return value;
	},

};
