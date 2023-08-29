// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Consolidation Report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label":__("From Date"),
			"fieldtype":"Date",
			"reqd":1,
			"default":frappe.datetime.year_start()
		},
		{
			"fieldname":"to_date",
			"label":__("To Date"),
			"fieldtype":"Date",
			"reqd":1,
			"default":frappe.datetime.month_end()
		},
		{
			"fieldname":"is_inter_company",
			"label":__("Is Inter Company"),
			"fieldtype":"Select",
			"options":['','Yes','No']
		},
		// {
		// 	"fieldname":"create_transaction",
		// 	"label":__("Create Transaction"),
		// 	"fieldtype":"Button",
		// 	"click":()=>{
		// 		// console.log(frappe.query_report.filters)
		// 		// let bol = confirm("<b>Are You sure you want to create new transaction with this data, this data will be send to dhi for consolidation</b>")
		// 		if (frappe.query_report.data){
		// 			frappe.call({
		// 				method: "erpnext.accounts.report.consolidation_report.consolidation_report.create_transaction",
		// 				args: {
		// 					'filters':frappe.query_report.filters,
		// 					'data': frappe.query_report.data
		// 				},
		// 				callback: function(r) {
		// 				}
		// 			});
		// 		}
		// 	}
		// }
	]
}
