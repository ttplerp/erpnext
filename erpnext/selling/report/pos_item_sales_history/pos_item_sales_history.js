// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["POS Item Sales History"] = {
	"filters": [
		{
			fieldname:"company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname:"from_date",
			reqd: 1,
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname:"to_date",
			reqd: 1,
			default: frappe.datetime.get_today(),
			label: __("To Date"),
			fieldtype: "Date",
		},
		{
			fieldname:"item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
			get_query: () => {
				return {
					query: "erpnext.controllers.queries.item_query"
				}
			}
		},
		{
			"fieldname":"pos_profile",
			"label": __("POS Profile"),
			"fieldtype": "Link",
			"options": "POS Profile"
		}
	]
};
