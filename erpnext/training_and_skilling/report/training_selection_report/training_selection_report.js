// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Training Selection Report"] = {
	"filters": [
		{
			"fieldname": "cohort",
			"label": __("Cohort"),
			"fieldtype": "Link",
			"options": "Cohort",
			"reqd": 1,
			//"get_query": function() {return {'filters': [['Cost Center', 'disabled', '!=', '1']]}}
		},
		{
			"fieldname": "course",
			"label": __("Course"),
			"fieldtype": "Link",
			"options": "Course",
			"reqd": 1,
			//"get_query": function() {return {'filters': [['Cost Center', 'disabled', '!=', '1']]}}
		},
	]
};
