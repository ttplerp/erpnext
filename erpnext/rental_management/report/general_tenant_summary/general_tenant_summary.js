// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["General Tenant Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		},
		{
			fieldname: "rental_official",
			label: __("Rental Focal"),
			fieldtype: "Link",
			width: "80",
			options: "Employee",
			get_query: function() {
				return {
					filters: [
						['Employee', 'user_id', 'in', ['dema@nhdcl.bt','bumpa.dema@nhdcl.bt','dm.ghalley@nhdcl.bt','rinzin.dema@nhdcl.bt','dorji.wangmo@nhdcl.bt']]
					]
				}
			},
			on_change: function(query_report) {
				var emp = query_report.get_filter_value('rental_official');
				if (!emp) {
					return;
				}
				frappe.db.get_value("Employee", emp, "employee_name", function(value) {
					frappe.query_report.set_filter_value('focal_name', value["employee_name"]);
				});
			}
		},
		{
			"fieldname": "focal_name",
			"label": __("Focal Name"),
			"fieldtype": "Data",
			"read_only": 1
		},
		// {
		// 	"fieldname":"employment_type",
		// 	"label": __("Employment Type"),
		// 	"fieldtype": "Select",
		// 	"options": ["", __("Civil Servant"), __("Corporate Employee"), __("Private Employee"), __("Others")],
		// 	on_change: function(query_report){
		// 		var employment_type = frappe.query_report.get_filter_value('employment_type');
		// 		if(employment_type == "Civil Servant"){
		// 			var ministry_agency = frappe.query_report.get_filter("ministry_agency"); 
		// 			ministry_agency.toggle(true);
		// 			frappe.query_report.set_filter_value('ministry_agency', "");
		// 		}else{
		// 			var ministry_agency = frappe.query_report.get_filter("ministry_agency"); 
		// 			ministry_agency.toggle(false);
		// 			frappe.query_report.set_filter_value('ministry_agency', "");	
		// 		}
				
		// 		query_report.trigger_refresh();	
		// 	},
		// 	"reqd":1,
		// 	"default":"Civil Servant"
		// },
		{
			"fieldname": "ministry_agency",
			"label": __("Ministry/Agency"),
			"fieldtype": "Link",
			"options": "Ministry and Agency"
		},
		{
			"fieldname": "dzongkhag",
			"label": __("Dzongkhag"),
			"fieldtype": "Link",
			"options": "Dzongkhag"
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"options": "Locations"
		},
		{
			"fieldname": "building_category",
			"label": __("Building Category"),
			"fieldtype": "Link",
			"options": "Building Category"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Tenant Department",
			on_change: function(query_report) {
				var dep = query_report.get_filter_value('department');
				if (!dep) {
					return;
				}
				frappe.db.get_value("Tenant Department", dep, "department", function(value) {
					frappe.query_report.set_filter_value('department_name', value["department"]);
				});
			}
		},
		{
			"fieldname": "department_name",
			"label": __("Department Name"),
			"fieldtype": "Data",
			"read_only": 1
		},
	]
};
