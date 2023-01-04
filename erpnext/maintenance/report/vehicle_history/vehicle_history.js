// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle History"] = {
	"filters": [
		{
			"fieldname": "equipment_no",
			"label": ("Equipment"),
			"fieldtype": "Link",
			"options": "Equipment",
			"reqd": 1

		},
		{
			"fieldname": "from_date",
			"label": ("From Date"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": ("To Date"),
			"fieldtype": "Date",
			"reqd": 1
		}
	]
}
