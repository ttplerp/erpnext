// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Equipment Maintenance History"] = {
	"filters": [
		{
		 "fieldname":"branch",
		 "label":("Branch"),
		 "fieldtype":"Link",
		 "options":"Branch",
		 "reqd":"1",
		},
		{
		  "fieldname":"from_date",
		  "label":("From Date"),
		  "fieldtype":"Date",
		  "width":"80",
		  "default": frappe.datetime.year_start()
		},
		{
		  "fieldname":"to_date",
		  "label":("To Date"),
		  "fieldtype":"Date",
		  "width":"80",
		  "default": frappe.datetime.year_end()
		},
		{
		 "fieldname":"equipment",
		 "label":("Equipment"),
		 "fieldtype":"Link",
		 "options":"Equipment"
		}
	]
}
