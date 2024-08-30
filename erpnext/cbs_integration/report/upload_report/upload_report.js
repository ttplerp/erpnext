// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Upload Report"] = {
	get_datatable_options(options){
		return Object.assign(options, {
			checkboxColumn: true
		});
	},
	onload: function(report){
		// report.page.add_action_item(__("Create CBS Entry"), function(){
		report.page.add_inner_button(__("Create CBS Entry"), function(){
			if(frappe.query_report.get_filter_value('cbs_entry')){
				frappe.set_route("Form", "CBS Entry", frappe.query_report.get_filter_value('cbs_entry'));
				return
			}
			if(!report.datatable){
				frappe.throw(__("Please select the transactions in order to create CBS Entry"))
			}

			let checked_rows_indexes = report.datatable.rowmanager.getCheckedRows();
			let checked_rows = checked_rows_indexes.map(i => report.data[i].voucher_type + "||"+ report.data[i].voucher_no);
			// let transaction_list = checked_rows.filter((item, i, ar) => ar.indexOf(item) === i);

			if(!checked_rows.length){
				frappe.throw(__("Please select the transactions in order to create CBS Entry"))
			}
			
			console.log("checked : " + checked_rows);

			frappe.prompt({
				fieldtype: 'Data',
				label: __('Entry Title'),
				fieldname: 'entry_title',
				description: __('* Title is mandatory for creating upload entry'),
				reqd: 1
			}, (data) => {
				frappe.call({
					method: "erpnext.cbs_integration.doctype.cbs_entry.cbs_entry.make_cbs_entry",
					args: {
						'entry_title': data.entry_title,
						'from_date': frappe.query_report.get_filter_value('from_date'),
						'to_date': frappe.query_report.get_filter_value('to_date'),
						'transaction_list': checked_rows
					},
					callback: function(r){
						if(r.message){
							frappe.set_route("Form", "CBS Entry", r.message);
						}
					},
					freeze: true,
					freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Creating CBS Entry.... Please Wait</span>',
				});	
			})
		}).addClass("btn-primary");
	}, 
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "voucher_type",
			"label": __("Voucher Type"),
			"fieldtype": "Link",
			"options": "Transaction Mapping",
			get_query: () => {
				return {
					filters: {
						'transaction_type': ['in', ['CASA', 'GL']]
					}
				}
			}
		},
		{
			"fieldname": "voucher_no",
			"label": __("Voucher No"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type"
		},
		{
			"fieldname":"cbs_entry",
			"label": __("CBS Entry"),
			"fieldtype": "Link",
			"options": "CBS Entry",
			get_query: () => {
				return {
					filters: {
						'docstatus': 1,
						'entry_type': 'Upload'
					}
				}
			},
			"hidden": 0
		},
		{
			"fieldname":"show_errors",
			"label": __("Show Errors"),
			"fieldtype": "Check",
			"default": 0,
			"hidden": 0
		},
	],
};
