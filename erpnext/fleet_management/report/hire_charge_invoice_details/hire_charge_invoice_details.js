// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Hire Charge Invoice Details"] = {
	"filters": [
		{
			"fieldname":"name",
			"label":__("Reference"),
			"fieldtype":"Link",
			"options":"Hire Charge Invoice",
			"reqd":1
		}
	]
};
