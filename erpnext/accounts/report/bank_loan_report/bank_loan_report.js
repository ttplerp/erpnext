// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Bank Loan Report"] = {
	"filters": [
		{
			fieldname:"parent_account",
			label: __("Parent Account"),
			fieldtype: "Link",
			options:"Account",
		},
		{
			fieldname:"account",
			label: __("Account"),
			fieldtype: "Link",
			options:"Account",
		},
		{
			fieldname:"fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options:"Fiscal Year"
			
		},
		{
            "fieldname": "monthly",
            "label": __("Monthly"),
            "fieldtype": "Select",
            "options": "\n01\n02\n03\n04\n05\n06\n07\n08\n09\n10\n11\n12",
            "default": "01"
        },
		{
			fieldname:"account_wise",
			label: __("Account Wise"),
			fieldtype: "Check",
			options:""
			
		},

	]
};
