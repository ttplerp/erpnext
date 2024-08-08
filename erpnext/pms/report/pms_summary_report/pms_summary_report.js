// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PMS Summary Report"] = {
	"filters": [
		{
			"fieldname":"branch",
			"label":"Branch",
			"fieldtype":"Link",
			"options":"Branch"
		},
		{
			"fieldname":"region",
			"label":"Region",
			"fieldtype":"Link",
			"options":"Region"
		},
		{
			"fieldname":"pms_calendar",
			"label":"PMS Calendar",
			"fieldtype":"Link",
			"options":"PMS Calendar"
		},
		{
			"fieldname":"pms_group",
			"label":"PMS Group",
			"fieldtype":"Link",
			"options":"PMS Group"
		},
		{
			"fieldname":"gender",
			"label":"Gender",
			"fieldtype":"Select",
			"options":['','Male','Female','Others']
		},
		{
			"fieldname":"rating",
			"label":"Rating",
			"fieldtype":"Link",
			"options":"Overall Rating"
		}
	]
};
