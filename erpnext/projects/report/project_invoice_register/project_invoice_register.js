// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Project Invoice Register"] = {
	"filters": [
        {
            "fieldname":"project",
            "label": ("Project"),
            "fieldtype": "Link",
            "options" : "Project"

    },
    {
            "fieldname":"from_date",
            "label": ("From Date"),
            "fieldtype": "Date",

    },
    {
            "fieldname":"to_date",
            "label": ("To Date"),
            "fieldtype": "Date",

    }
	]
};
