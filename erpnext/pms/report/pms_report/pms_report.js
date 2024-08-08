// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PMS Report"] = {
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
				"fieldname":"workflow_state",
				"label": __("Status"),
				"fieldtype": "Select",
				"options": ["", "Draft", "Waiting Approval", "Approved", "Rejected"],
				"default":"Approved"
			},
			{
				"fieldname":"docstatus",
				"label": __("Status"),
				"fieldtype": "Select",
				"options": ["", "Draft", "Submitted"],
				"default":"Approved",
				"hidden" : 1
			},	
			{
				"fieldname":"type",
				"label": __("Report Type"),
				"fieldtype": "Select",
				"options": ["Target Setup Report", "Review Report","Performance Evaluation Report","PMS Summary"],
				"default":"Performance Evaluation Report",
				"reqd": 1,
				on_change:function(query_report){
					var type = query_report.get_filter_value('type')
					if (type == "Performance Evaluation Report"){
						var workflow_state = query_report.get_filter("workflow_state"); workflow_state.toggle(true);
						var docstatus = query_report.get_filter("docstatus"); docstatus.toggle(false);
						query_report.get_filter('reason').toggle(type == "Performance Evaluation Report" ? 1:0)
						query_report.get_filter('from_date').toggle(type == "Performance Evaluation Report" ? 1:0)
						query_report.get_filter('to_date').toggle(type == "Performance Evaluation Report" ? 1:0)
					} 
					else if (type == "PMS Summary"){
						var workflow_state = query_report.get_filter("workflow_state"); workflow_state.toggle(false);
						var docstatus = query_report.get_filter("docstatus"); docstatus.toggle(true);
					} 
					else {
						query_report.get_filter('reason').toggle(type == "Performance Evaluation Report" ? 0:1)
						query_report.get_filter('from_date').toggle(type == "Performance Evaluation Report" ? 0:1)
						query_report.get_filter('to_date').toggle(type == "Performance Evaluation Report" ? 0:1)
						var workflow_state = query_report.get_filter("workflow_state"); workflow_state.toggle(true);
						var docstatus = query_report.get_filter("docstatus"); docstatus.toggle(false);
					}
					frappe.query_report.refresh()	
				}
			},
			{
				"fieldname":"branch",
				"label": __("Branch"),
				"fieldtype": "Link",
				"options": "Branch",				
				"reqd": 0
			},
			{
				"fieldname":"department",
				"label": __("Department"),
				"fieldtype": "Link",
				"options": "Department",				
				"reqd": 0
			},
			{
				"fieldname":"division",
				"label": __("Division"),
				"fieldtype": "Link",
				"options": "Division",				
				"reqd": 0
			},
			{
				"fieldname":"region",
				"label": __("Region"),
				"fieldtype": "Link",
				"options": "Region",				
				"reqd": 0
			},	
			{
				"fieldname":"section",
				"label": __("Section"),
				"fieldtype": "Link",
				"options": "Section",				
				"reqd": 0
			},	
			{
				"fieldname":"unit",
				"label": __("Unit"),
				"fieldtype": "Link",
				"options": "Unit",				
				"reqd": 0
			},
			{
				"fieldname":"reason",
				"label": __("Reason"),
				"fieldtype": "Select",
				"options": "\nChange In Section/Division/Department\nSuperannuation/Left\nTransfer\nChange In PMS Group",				
				"hidden": 0
			},
			{
				"fieldname":"from_date",
				"label": __("Appointed From Date"),
				"fieldtype": "Date",
				"hidden":0
			},
			{
				"fieldname":"to_date",
				"label": __("Appointed To Date"),
				"fieldtype": "Date",
				"hidden":0
			},
			{
				"fieldname":"gender",
				"label": __("Gender"),
				"fieldtype": "Select",
				"options": ["","Male", "Female"],				
				"reqd": 0
			},
	]
};
