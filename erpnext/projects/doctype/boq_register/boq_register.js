// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["BOQ Register"] = {
	"filters": [
        {
			"fieldname":"project",
			"label": ("Project"),
			"fieldtype": "Link",
			"options" : "Project"

		},

		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.defaults.get_user_default("year_start_date"),

		},

		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",

		}
	]
};
