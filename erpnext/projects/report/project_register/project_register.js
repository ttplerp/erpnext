// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Project Register"] = {
	"filters": [
        {
			"fieldname": 	"project",
			"label": 		("Project"),
			"fieldtype": 	"Link",
			"options":		"Project"			
		},
		{
			"fieldname": 	"branch",
			"label": 		("Branch"),
			"fieldtype": 	"Link",
			"options":		"Branch"
		},
		{
			"fieldname": 	"cost_center",
			"label": 		("Cost Center"),
			"fieldtype": 	"Link",
			"options":		"Cost Center"
		},		
		{
			"fieldname":	"from_date",
			"label":		("From Date"),
			"fieldtype":	"Date",
			"reqd":0
		},
		{
			"fieldname":	"to_date",
			"label":		("To Date"),
			"fieldtype":	"Date",
			"reqd":0
		},
		{
			"fieldname":	"additional_info",
			"label":		("Additional Information"),
			"fieldtype":	"Check",
			"reqd":			0
		},	
	]
};
