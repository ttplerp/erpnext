// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Deployment Report"] = {
	"filters": [
		{
			"fieldname": "did",
			"label": __("Desuung ID"),
			"fieldtype": "Link",
			"options": "Desuup",
			"reqd": 1,
		},
	]
};
