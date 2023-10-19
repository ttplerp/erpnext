// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rental Increment Report"] = {
	"filters": [
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: frappe.defaults.get_user_default("fiscal_year"),
			reqd: 1,
		},
		{
			fieldname: "month",
			label: "Month",
			fieldtype: "Select",
			options: ["1","2","3","4","5","6","7","8","9","10","11","12"],
			default: "",
			reqd: 1,
		},
		{
			"fieldname": "ministry_and_agency",
			"label": __("Ministry and Agency"),
			"fieldtype": "Link",
			"options": "Ministry and Agency"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Tenant Department"
		},
	]
};
