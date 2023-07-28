frappe.require("assets/erpnext/js/financial_statements.js", function() {
    frappe.query_reports["Business Review Report"] = {
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
                "fieldname": "current_from_date",
                "label": __("From Date"),
                "fieldtype": "Date",
                "reqd": 1
            },
            {
                "fieldname": "current_to_date",
                "label": __("To Date"),
                "fieldtype": "Date",
                "reqd": 1
            },
            // {
            //     "fieldname": "cost_center",
            //     "label": __("Cost Center"),
            //     "fieldtype": "MultiSelectList",
            //     get_data: function(txt) {
            //         return frappe.db.get_link_options('Cost Center', txt);
            //     }
            // },
            {
                "fieldname": "include_default_book_entries",
                "label": __("Include Default Book Entries"),
                "fieldtype": "Check",
                "default": "1",
            },
            {
                "fieldname": "comparison_from_date",
                "label": __("Comparison From Date"),
                "fieldtype": "Date",
                "reqd": 1
            },
            {
                "fieldname": "comparison_to_date",
                "label": __("Comparison To Date"),
                "fieldtype": "Date",
                "reqd": 1
            },
        ],
        "formatter": erpnext.financial_statements.formatter,
        "tree": true,
        "name_field": "account",
        "parent_field": "parent_account",
        "initial_depth": 3
    };
});
