// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Desuung Sales Report"] = {
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
		},
		{
			fieldname: "desuupid",
			fieldtype: "Link",
			options: "Desuup",
			label: "Desuup ID",
			width: 100
		}
	]
};
