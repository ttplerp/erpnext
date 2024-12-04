// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Depreciation Schedule Report"] = {
	"filters": [
		{
			"fieldname":"report_type",
			"label": __("Report"),
			"fieldtype": "Select",
			"reqd": 1,
			"options": ['Monthly Summary', 'Schedule Details'],
			"on_change": function(){
				var query_report = frappe.query_report;
				var report_type = query_report.get_filter_value('report_type');
				if(report_type == 'Monthly Summary'){
					query_report.get_filter('month').toggle(false);
				} else if(report_type == 'Schedule Details'){
					query_report.get_filter('month').toggle(true);
				}
				// query_report.get_filter('cbs_entry').refresh();
				// query_report.refresh();
			}

		},
		{
			"fieldname":"fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"reqd": 1,
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
		},
		{
			"fieldname":"month",
			"label": __("Month"),
			"fieldtype": "Select",
			"hidden": 1,
			"options": ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
		},
	]
};
