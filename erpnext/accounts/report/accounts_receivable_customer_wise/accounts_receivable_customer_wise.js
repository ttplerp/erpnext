// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Accounts Receivable Customer Wise"] = {
	"filters": [
		{
			fieldname:"individual",
			label: __("Individual"),
			fieldtype: "Check",
			options:""
			
		},
		{
			fieldname:"customer",
			label: __("Customer"),
			fieldtype: "Link",
			options:"Customer",
		},
		{
			fieldname:"cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options:"Cost Center",
		},
		{
			fieldname:"fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options:"Fiscal Year",
		},

	]
};
