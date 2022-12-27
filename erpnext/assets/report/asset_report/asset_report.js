// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Asset Report"] = {
	"filters": [
		{
			"fieldname":"status",
			"label": "Status",
			"fieldtype":"Select",
			"options": [" ", "Draft", "Partially Depreciated","Depreciated","Scrapped"]
		},
		{
			"fieldname":"asset_category",
			"label": "Asset Category",
			"fieldtype":"Link",
			"options": "Asset Category"
		}
	],
};
