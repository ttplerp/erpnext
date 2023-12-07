// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Deviation Item Statement"] = {
	"filters": [
		{
			"fieldname":"project",
			"fieldtype":"Link",
			"label":__("Project"),
			"options":"Project",
			"reqd":0
		},
		{
			"fieldname":"boq",
			"fieldtype":"Link",
			"label":__("BOQ"),
			"options":"BOQ",
			"reqd":0
		},
		{
			"fieldname":"from_date",
			"fieldtype":"Date",
			"label":__("From Date"),
			"default":frappe.datetime.month_start(),
			"reqd":1
		},
		{
			"fieldname":"to_date",
			"fieldtype":"Date",
			"label":__("To Date"),
			"default":frappe.datetime.month_end(),
			"reqd":1
		},
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && column.id == "name" ) {
			value = "<span style='color:black!important; font-weight:bold'; font-style: italic !important;'>" + value + "</span>";
		}
		return value;
	},
};
