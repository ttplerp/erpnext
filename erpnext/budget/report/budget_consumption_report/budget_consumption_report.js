// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Budget Consumption Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
		},
		{
			"fieldname": "fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1,
			"on_change": function(query_report) {
				var fiscal_year = query_report.get_values().fiscal_year;
				if (!fiscal_year) {
					return;
				}
				frappe.model.with_doc("Fiscal Year", fiscal_year, function(r) {
					var fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
					query_report.filters_by_name.from_date.set_input(fy.year_start_date);
					query_report.filters_by_name.to_date.set_input(fy.year_end_date);
					query_report.trigger_refresh();
				});
			}
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.defaults.get_user_default("year_start_date"),
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.defaults.get_user_default("year_end_date"),
		},
		{
			"fieldname": "cost_center",
			"label": __("Parent Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"reqd":1,
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return {'filters': [
					['Cost Center', 'disabled', '!=', '1'],
					['Cost Center', 'is_group', '=', '1'],
					['Cost Center', 'company', '=', company]
				]
			}},
		},
		{
			"fieldname": "branch_cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"get_query": function() {
				var cost_center = frappe.query_report.get_filter_value('cost_center');
				return {'filters': [['Cost Center', 'disabled', '!=', '1'],['Cost Center', 'parent_cost_center', '=', cost_center]]}
			},
		},
		{
			"fieldname": "business_activity",
			"label": __("Business Activity"),
			"fieldtype": "Link",
			"options": "Business Activity",
			"reqd":1,
			"get_query": function() {
				var company = frappe.query_report.get_filter_value('company');
				return {'filters': [
					['Business Activity', 'company', '=', company]
				]
			}},
		},
		{
			"fieldname": "group_by_account",
			"label": __("Group By Account"),
			"fieldtype": "Check",
			"default": 0,
		},
	],
	onload: function(report) {
		report.page.add_inner_button(__("Detailed Budget Consumption Report"), function() {
			var filters = report.get_values();
			frappe.route_options = {
				"company": filters.company,
				"cost_center": filters.cost_center,
				"branch_cost_center": filters.branch_cost_center,
				"business_activity": filters.business_activity,
			};
			frappe.set_route('query-report', 'Detailed Budget Consumption Report');
		});
	}
   }

