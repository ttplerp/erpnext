// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Asset Final Schedule Detail"] = {
	"filters": [
		{
			"fieldname":"schedule_date",
			"label": __("Schedule Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"asset_category",
			"label": __("Asset Category"),
			"fieldtype": "Link",
			"options": "Asset Category"
		}
	]
};
