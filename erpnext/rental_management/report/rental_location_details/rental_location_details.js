// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rental Location Details"] = {
	"filters": [
		{
			"fieldname": "location",
			"label": __("Location ID"),
			"fieldtype": "Link",
			"options": "Locations"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["Allocated","Unallocated"]
		},
		{
			"fieldname": "block_no",
			"label": __("Block No"),
			"fieldtype": "Link",
			"options": "Block No"
		},
		
	]
};
