// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Asset Register"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Select",
			"options": ["", __("2023"), __("2024"), __("2025"),__("2026"), __("2027"), __("2028"),__("2029"), __("2030")],
			"reqd": 1,
			
			"on_change": function(query_report) {
				var fiscal_year = query_report.get_values().fiscal_year;
				var year_start_date = fiscal_year+"-01-01" //"01-01-"+fiscal_year 
				var year_end_date = fiscal_year+"-12-31" //"31-12-"+fiscal_year
				console.log(year_start_date);
				query_report.set_filter_value({
					from_date: year_start_date,
					to_date: year_end_date
				});
				//query_report.filters_by_name.from_date.set_input(year_start_date);
				//query_report.filters_by_name.to_date.set_input(year_end_date); 
				frappe.query_report.trigger_refresh();
			} 
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			//"default": frappe.defaults.get_user_default("year_start_date"),
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			//"default": frappe.defaults.get_user_default("year_end_date"),
		},
		//Custom filter to query based on "Cost Center"
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"reqd": 1,
		},
		{
			"fieldname": "asset_category",
			"label": __("Asset Category"),
			"fieldtype": "Link",
			"options": "Asset Category",
		},
		//  1869
		{
			"fieldname": "asset_code",
			"label": __("Asset Code"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Asset', txt);
			}
		},

	]
}

