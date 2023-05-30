// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Equipment Hire Report"] = {
	"filters": [
		{
			"fieldname": "branch",
			"label": ("Branch"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Branch",
		},
		{
			"fieldname":"from_date",
			"label": ("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname":"to_date",
			"label": ("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options": "DocType",
			"get_query": function() {
				return {
					filters: {"name": ["in", ["Customer", "Supplier"]]}
				}
			}
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "Dynamic Link",
			"get_options": function() {
				var party_type = frappe.query_report.get_filter_value('party_type');
				var party = frappe.query_report.get_filter_value('party');
				if(party && !party_type) {
					frappe.throw(__("Please select Party Type first"));
				}
				return party_type;
			}
		},
		{
			"fieldname": "not_nhdcl",
			"label": ("Include Only Own Company"),
			"fieldtype": "Check",
			"default": 1
		},
		{
			"fieldname": "include_disabled",
			"label": ("Include Disabled Equipments"),
			"fieldtype": "Check",
			"default": 0
		},

	]
}

