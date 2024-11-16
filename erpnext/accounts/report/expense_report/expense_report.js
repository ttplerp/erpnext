// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Expense Report"] = {
	"filters": [
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
			default:"2024"
			
		},
		{
            "fieldname": "monthly",
            "label": __("Monthly"),
            "fieldtype": "Select",
            "options": "\n01\n02\n03\n04\n05\n06\n07\n08\n09\n10\n11\n12",
            "default": " "
        },

	]
};
