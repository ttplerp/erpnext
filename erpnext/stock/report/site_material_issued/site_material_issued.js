// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Site Material Issued"] = {
	"filters": [
		{
			"fieldname": "site_name",
			"label": __("Site"),
			"fieldtype": "Link",
			"options": "Site Name",
		},
		{
			"fieldname": "requisition_type",
			"label": __("Requisition Type"),
			"fieldtype": "Select",
			"options": ["", "Material Issue", "Purchase", "Material Transfer"]
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},

	]
};
