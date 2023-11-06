// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["PMS Average Report"] = {
	"filters": [
		{
			"fieldname": "pms_calendar",
			"label": __("PMS Year"),
			"fieldtype": "Link",
			"options": "PMS Calendar",				
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1
		},			
		{
			"fieldname":"average",
			"label": __("Average Based On"),
			"fieldtype": "Select",
			"options": ["","Section","Unit","Region","Division","Cost Center","Department"],
			"reqd": 0,
			on_change:function(query_report){
				var average = frappe.query_report.get_filter_value('average');
				frappe.query_report.get_filter('section').toggle(average == 'Section' ? 1:0)
				frappe.query_report.get_filter('unit').toggle(average == 'Unit' ? 1:0)
				frappe.query_report.get_filter('region').toggle(average == 'Region' ? 1:0)
				frappe.query_report.get_filter('division').toggle(average == 'Division' ? 1:0)
				frappe.query_report.get_filter('cost_center').toggle(average == 'Cost Center' ? 1:0)
				frappe.query_report.get_filter('department').toggle(average == 'Department' ? 1:0)
				frappe.query_report.refresh()
			}
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
			"reqd": 0,
		},
		{
			"fieldname":"region",
			"label": __("Region"),
			"fieldtype": "Link",
			"options": "Region",				
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
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",				
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
			"fieldname":"gender",
			"label": __("Gender"),
			"fieldtype": "Select",
			"options": ["","Male", "Female"],				
			"reqd": 0
		},
		{
			"fieldname":"exclude_approver",
			"label": __("Exclude Approver"),
			"fieldtype": "Check",
			"options": "Approver",
			"reqd": 0
		},				
	]
};
