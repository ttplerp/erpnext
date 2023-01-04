// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Reimbursement Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: "From Date",
			width: 100,
			reqd: 1
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: "To Date",
			width: 100,
			reqd: 1
		}
	]
}
