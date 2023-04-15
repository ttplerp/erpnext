// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Individual Soelra Report"] = {
	"filters": [
		{
			fieldname: "desuupid",
			fieldtype: "Link",
			options: "Desuup",
			label: "Desuup ID",
			width: 100,
			on_change: function(query_report) {
				var desuup = query_report.get_filter_value('desuupid')
				if (!desuup) {
					return;
				}
				frappe.db.get_value("Desuup", desuup, "desuup_name", function(value) {
					frappe.query_report.set_filter_value('dname', value["desuup_name"]);
				});
			}
		},
		{
			fieldname: "dname",
			fieldtype: "Data",
			label: "Name",
			width: 100
		},
		{
			fieldname: "others",
			fieldtype: "Data",
			label: "Others",
			width: 100
		}
	]
};
