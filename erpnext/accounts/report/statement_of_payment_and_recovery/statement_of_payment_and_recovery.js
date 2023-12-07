// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Statement of Payment and Recovery"] = {
	"filters": [
		{
			"fieldname":"project",
			"fieldtype":"Link",
			"label":__("Project"),
			"options":"Project",
			"reqd":0
		},
		{
			"fieldname":"branch",
			"fieldtype":"Link",
			"label":__("Branch"),
			"options":"Branch",
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
	]
};
