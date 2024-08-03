// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Payable Account Supplier Wise"] = {
	"filters": [

		{
			fieldname:"individual",
			label: __("Individual"),
			fieldtype: "Check",
			options:""
			
		},
		{
			fieldname:"supplier",
			label: __("Supplier Type"),
			fieldtype: "Select",
			options:"\nDomestic Vendor\nInternational Vendor\nIndividual",
		},

	]
};
