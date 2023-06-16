// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Desuung Undergone DSP"] = {
	"filters": [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: "From Date",
			width: 100,
			reqd: 1,
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: "To Date",
			width: 100,
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "domain",
			label: __("Domain"),
			fieldtype: "Link",
			options: "DSP Domain",
			default:""
		},
		{
			fieldname: "programme",
			label: __("Programme"),
			fieldtype: "Link",
			options: "Programme",
			default:""
		},
		{
			fieldname: "did",
			label: __("Desuung ID"),
			fieldtype: "Link",
			options: "Desuup",
			default:""
		},
	]
};
