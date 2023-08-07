frappe.require("assets/erpnext/js/financial_statements.js", function() {
    frappe.query_reports["Business Review Report"] = {
        onload: function(report) {
            report.page.add_inner_button(__("Key Indicators and Drivers Report"), function() {
                var filters = report.get_values();
                frappe.route_options = {
                    "current_from_date": filters.current_from_date,
                    "current_to_date": filters.current_to_date,
                    "comparison_from_date": filters.comparison_from_date,
                    "comparison_to_date": filters.comparison_to_date,
                    "include_default_book_entries": filters.include_default_book_entries,
                };
                frappe.set_route('query-report', 'Key Indicators and Drivers Report');
            });
        },
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
