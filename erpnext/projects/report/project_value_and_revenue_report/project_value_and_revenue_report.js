// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Project Value and Revenue Report"] = {
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
			"fieldname":"is_active",
			"fieldtype":"Select",
			"label":__("Is Active"),
			"options":["Yes", "No"],
			"reqd":0
		},
	]
};
