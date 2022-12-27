// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Asset Transfer Report"] = {
	"filters": [
		{
			"fieldname": "purpose",
			"label": __("Purpose"),
			"fieldtype": "Select",
			"options": [" ","Transfer", "Receipt","Issue"],
		},
	],
};
