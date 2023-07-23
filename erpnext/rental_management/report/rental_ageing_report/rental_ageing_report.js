// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rental Ageing Report"] = {
	"filters": [
		{
			"fieldname": "date",
			"label": __("Date"),
			"fieldtype": "Date",
			"reqd":1,
			"read_only": 1,
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname":"based_on",
			"label": __("Based On"),
			"fieldtype": "Select",
			"options": ["", __("Tenant"), __("Dzongkhag")],
			on_change: function(query_report){
				var based_on = frappe.query_report.get_filter_value('based_on');
				if(based_on == "Dzongkhag"){
					var dzongkhag = frappe.query_report.get_filter("dzongkhag"); dzongkhag.toggle(false);
					frappe.query_report.set_filter_value('dzongkhag', "");
				}else{
					var dzongkhag = frappe.query_report.get_filter("dzongkhag"); dzongkhag.toggle(true);
					frappe.query_report.set_filter_value('dzongkhag', "");		
				}
				
				query_report.trigger_refresh();	
			},
			"reqd":1,
			"default":"Tenant"
		},
		{
			"fieldname": "dzongkhag",
			"label": __("Dzongkhag"),
			"fieldtype": "Link",
			"options": "Dzongkhag",
		},
	]
};
