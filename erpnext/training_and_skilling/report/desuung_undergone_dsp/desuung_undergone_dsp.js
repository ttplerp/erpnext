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
			options: "Programme Classification",
			default:""
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
		    options:["", __("Passed"), __("Withdrawn"), __("Terminated"), __("Suspended"), __("Attendance Shortage"), __("Reported")],
			default:""
		},
		{
			fieldname: "did",
			label: __("Desuung ID"),
			fieldtype: "Link",
			options: "Desuup",
			default:""
		},
		{
			fieldname: "detail",
			label: __("Detail"),
			fieldtype: "Check",
			default:"0"
		},
	]
};
