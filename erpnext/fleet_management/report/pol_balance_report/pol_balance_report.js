// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["POL Balance Report"] = {
	"filters": [
		{
			fieldname:"company", 
			label:__("Company"), 
			fieldtype:"Link", 
			options:"Company", 
			default: frappe.defaults.get_default("company"),
			reqd:1
		},
		{
			fieldname:"from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_start(),
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today()
		},
		{
			fieldname:"equipment",
			label: __("Tank"),
			fieldtype: "Link",
			options:"Equipment",
			get_query: () => {
				return {
					filters: {
						is_container:1,
						enabled:1,
						company:frappe.query_report.get_filter_value('company')
					}
				}
			}
		},
		{
			fieldname:"branch", 
			label:__("Branch"), 
			fieldtype:"Link", 
			options:"Branch"
		},
	]
};
