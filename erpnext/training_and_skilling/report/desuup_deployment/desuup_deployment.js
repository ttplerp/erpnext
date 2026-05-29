// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Desuup Deployment"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
		},
		{
			"fieldname": "deployment",
			"label": __("Deployment"),
			"fieldtype": "Link",
			"options": "Desuup Deployment",
			"get_query": function() {
				return {
				    filters: {
					type_of_deployment: ["!=", "Skilling"],
				    }
				};
			    }
		},
		{
			"fieldname": "dzongkhag",
			"label": __("Dzongkhag"),
			"fieldtype": "Link",
			"options": "Dzongkhags",
		},
		{
			"fieldname": "show",
			"label": __("Show by"),
			"fieldtype": "Select",
			"options": "Deployment\nDesuup",
			"default": "Deployment"
		},

	]
};
