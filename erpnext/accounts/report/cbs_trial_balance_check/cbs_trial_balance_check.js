// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CBS Trial Balance Check"] = {
	"filters": [
		{
			"fieldname":"report_date",
			"label": __("Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "100px"
		},
		{
			"fieldname":"sol_id",
			"label": __("SOL ID"),
			"fieldtype": "Data",
		},
	]
};
