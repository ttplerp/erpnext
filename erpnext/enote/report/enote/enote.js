// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["eNote"] = {
	"filters": [
		{
			"fieldname": "enote_type",
			"label": __("eNote Type"),
			"fieldtype": "Link",
			"options": "eNote Type"
		},
		{
			"fieldname": "category",
			"label": __("eNote Category"),
			"fieldtype": "Select",
			"options": "\nNote Sheet\nCircular\nNotification\nInternal Memo\nOffice Order\nOfficial Letter"
		},
	]
};
