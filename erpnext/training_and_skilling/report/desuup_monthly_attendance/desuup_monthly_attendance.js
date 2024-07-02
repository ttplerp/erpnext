// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Desuup Monthly Attendance"] = {
	"filters": [
		{
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Select",
			"reqd": 1
		},
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"reqd": 1 ,
			"options": [
				{ "value": 1, "label": __("Jan") },
				{ "value": 2, "label": __("Feb") },
				{ "value": 3, "label": __("Mar") },
				{ "value": 4, "label": __("Apr") },
				{ "value": 5, "label": __("May") },
				{ "value": 6, "label": __("June") },
				{ "value": 7, "label": __("July") },
				{ "value": 8, "label": __("Aug") },
				{ "value": 9, "label": __("Sep") },
				{ "value": 10, "label": __("Oct") },
				{ "value": 11, "label": __("Nov") },
				{ "value": 12, "label": __("Dec") },
			],
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
		},
		{
			"fieldname":"report_for",
			"label": __("Report For"),
			"fieldtype": "Select",
			// "reqd": 1
			"options": "\nTrainee\nOJT"
		},
		// {
		// 	"fieldname": "document_type",
		// 	"label": _("Document Type"),
		// 	"fieldtype": "Select",
		// 	"width": 220,
		// 	"options": "\nTraining Management\nDesuup Deployment Entry"
		// },
		// {
		// 	"fieldname": "document",
		// 	"label": _("Document"),
		// 	"fieldtype": "Dynamic Link",
		// 	"options": "document_type",
		// 	"width": 220,
		// },
		{
			"fieldname":"desuup",
			"label": __("Desuup"),
			"fieldtype": "Link",
			"options": "Desuup",
			// get_query: () => {
			// 	var company = frappe.query_report.get_filter_value('company');
			// 	return {
			// 		filters: {
			// 			'company': company
			// 		}
			// 	};
			// }
		},
	], 

	onload: function() {
		return  frappe.call({
			method: "erpnext.training_and_skilling.report.desuup_monthly_attendance.desuup_monthly_attendance.get_attendance_years",
			callback: function(r) {
				var year_filter = frappe.query_report.get_filter('year');
				year_filter.df.options = r.message;
				year_filter.df.default = r.message.split("\n")[0];
				year_filter.refresh();
				year_filter.set_input(year_filter.df.default);
			}
		});
	},
};
