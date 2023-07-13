// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Vehicle Request History Report"] = {
	"filters": [
		{
			"fieldname":"branch",
			"fieldtype":"Link",
			"label":__("Branch"),
			"options":"Branch",
			"reqd":0
		},
		{
			"fieldname":"vehicle_type",
			"fieldtype":"Link",
			"label":__("Equipment Type"),
			"options":"Equipment Type"
		},
		{
			"fieldname":"from_date",
			"fieldtype":"Datetime",
			"label":__("From Date"),
			"default":frappe.datetime.month_start(),
			"reqd":1
		},
		{
			"fieldname":"to_date",
			"fieldtype":"Datetime",
			"label":__("To Date"),
			"default":frappe.datetime.month_end(),
			"reqd":1
		}
	]
};
