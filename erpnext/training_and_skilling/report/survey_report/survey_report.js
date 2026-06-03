// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Survey Report"] = {
	"filters": [
		{
			"fieldname": "survey",
			"label": __("Survey"),
			"fieldtype": "Link",
			"options": "Questionaire",
			"reqd": 1,
			"get_query": function() {
				return {
				    filters: {
					"is_active": 1
				    }
				};
			    }
		},
	]
};
