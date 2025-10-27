// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Upload Asset Report"] = {
	onload: function(report){
		report.page.add_inner_button(__("Download File"), function(){
				frappe.call({
					method: "erpnext.assets.report.upload_asset_report.upload_asset_report.generate_download_file",
					args: {
						'fiscal_year': frappe.query_report.get_filter_value('fiscal_year'),
						'month': frappe.query_report.get_filter_value('month'),
						'asset_category': frappe.query_report.get_filter_value('asset_category')
					},
					callback: function(r){
						if (r.message && r.message.file_url) {
							window.open(r.message.file_url);
						}
					},
					freeze: true,
					freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Creating CBS Entry.... Please Wait</span>',
				});	
		}).addClass("btn-primary");
	}, 
	"filters": [
		{
			"fieldname": "asset_category",
			"label": __("Asset Category"),
			"fieldtype": "Link",
			"options": "Asset Category",
			"reqd": 1,
		},
		{
			"fieldname": "fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
			"reqd": 1,
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				{ "value": "01", "label": __("January") },
				{ "value": "02", "label": __("Febuary") },
				{ "value": "03", "label": __("March") },
				{ "value": "04", "label": __("April") },
				{ "value": "05", "label": __("May") },
				{ "value": "06", "label": __("June") },
				{ "value": "07", "label": __("July") },
				{ "value": "08", "label": __("August") },
				{ "value": "09", "label": __("September") },
				{ "value": "10", "label": __("October") },
				{ "value": "11", "label": __("November") },
				{ "value": "12", "label": __("December") },
			],
			reqd: 1
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
		},

	]
};
