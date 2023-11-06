// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Target Setup Report"] = {
	"filters": [
			{
				"fieldname": "pms_calendar",
				"label": __("Fiscal Year"),
				"fieldtype": "Link",
				"options": "Fiscal Year",				
				"default": frappe.defaults.get_user_default("fiscal_year"),
				"reqd": 1
		    },			
			{
				"fieldname":"docstatus",
				"label": __("Status"),
				"fieldtype": "Select",
				"options": ["","Submitted", "Draft"]
			},	
			{
				"fieldname":"type",
				"label": __("Report Type"),
				"fieldtype": "Select",
				"options": ["Target Setup Report", "Review Report","Performance Evaluation Report"],
				"default": ["Target Setup Report"],
				"reqd": 1
			},
			{
				"fieldname":"branch",
				"label": __("Branch"),
				"fieldtype": "Link",
				"options": "Branch",				
				"reqd": 0
			},
				
					
		
	]
};
