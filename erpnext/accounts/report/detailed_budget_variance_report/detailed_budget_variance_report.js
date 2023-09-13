// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/erpnext/js/financial_statements.js", function() {
    frappe.query_reports["Detailed Budget Variance Report"] = {
        "filters": [
            {
                "fieldname": "company",
                "label": __("Company"),
                "fieldtype": "Link",
                "options": "Company",
                "default": frappe.defaults.get_user_default("Company"),
                "reqd": 1
            },
            {
                "fieldname": "from_date",
                "label": __("From Date"),
                "fieldtype": "Date",
                "reqd": 1
            },
            {
                "fieldname": "to_date",
                "label": __("To Date"),
                "fieldtype": "Date",
                "reqd": 1
            },
            {
                "fieldname": "include_default_book_entries",
                "label": __("Include Default Book Entries"),
                "fieldtype": "Check",
                "default": "1",
            },
			{
				"fieldname": "budget_against",
				"label": __("Budget Against"),
				"fieldtype": "Select",
				"options": ["Cost Center"],
				"default": "Cost Center",
				"read_only": 1,
				on_change: function() {
					frappe.query_report.set_filter_value("budget_against_filter", []);
					frappe.query_report.refresh();
				}
			},
			{
				"fieldname":"budget_against_filter",
				"label": __('Dimension Filter'),
				"fieldtype": "MultiSelectList",
				get_data: function(txt) {
					if (!frappe.query_report.filters) return;
	
					let budget_against = frappe.query_report.get_filter_value('budget_against');
					if (!budget_against) return;
	
					return frappe.db.get_link_options(budget_against, txt);
				}
			},
        ],
		"formatter": function (value, row, column, data, default_formatter) {
			value = default_formatter(value, row, column, data);
	
			if (column.fieldname.includes('variance')) {
	
				if (data[column.fieldname] < 0) {
					value = "<span style='color:red'>" + value + "</span>";
				}
				else if (data[column.fieldname] > 0) {
					value = "<span style='color:green'>" + value + "</span>";
				}
			}
	
			return value;
		},
        "tree": true,
        "name_field": "account",
        "parent_field": "parent_account",
        "initial_depth": 3
    };
});
