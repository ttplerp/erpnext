// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Progress Report"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": ("Company"),
			"fieldtype": "Link",
 			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "item_sub_group",
			"label": ("Item Sub Group"),
			"fieldtype": "Link",
 			"options": "Item Group",
			"reqd": 1,
			"get_query": function () {
				return {
					filters: {
						"parent_item_group": "Mines Product",
						"is_sub_group":1
					}
				};
			},
		},
		{
			"fieldname": "fiscal_year",
			"label": ("Fiscal Year"),
			"fieldtype": "Link",
 			"options": "Fiscal Year",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("fiscal_year"),
		},
		{
			"fieldname": "periodicity",
			"label": ("Periodicity"),
			"fieldtype": "Select",
 			"options": ["Monthly","Quarterly","Half-Yearly","Yearly"],
			"reqd": 1,
			"default":"Monthly"
		},
		{
			"fieldname": "filter_based_on",
			"label": __("Filter Base On"),
			"fieldtype": "Select",
			"options": ["Fiscal Year","Date Range"],
			"default":"Fiscal Year",
			"hidden":1
		},
		// {
		// 	"fieldname": "chart_base_on",
		// 	"label": __("Chart Base On"),
		// 	"fieldtype": "Select",
		// 	"options": ["Target Qty(MT)","Achieved Qty (MT)","Progress(%)","Cumulative (Sales)","Cumulative Sales Progress(%)"],
		// 	"default":"Progress(%)",
		// },
		
	],
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && column.id == "particulars" ) {
			value = "<span style='font-weight:bold'; font-style: italic !important;'>" + value + "</span>";
			}
		return value;
	},
};
