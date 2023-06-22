// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Revenue Target"] = {
	"filters": [
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year"
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center"
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
			"default": get_today(),
		},
		{
			"fieldname": "monthly",
			"label": __("Monthly"),
			"fieldtype": "Check",
			"default": 1,
			"on_change": function (query_report) {
				var monthly = query_report.get_values().monthly;
				var month_filter = query_report.get_filter("month");
				if (monthly) {
					month_filter.toggle(true);
				}
				else {
					month_filter.toggle(false);
				}
				query_report.refresh();
			}
		},
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"width": "100",
			"options": ["January","February","March","April","May","June","July","August","September","October","November","December"],
		}
	]
};
