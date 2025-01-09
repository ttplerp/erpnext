frappe.query_reports["Daily Work Report"] = {
    "filters": [
        {
            fieldname: "cost_center",
            label: __("Cost Center"),
            fieldtype: "Link",
            options: "Cost Center",
        },
        {
            fieldname: "project",
            label: __("Project"),
            fieldtype: "Link",
            options: "Project",
            get_query: function () {
                let cost_center = frappe.query_report.get_filter_value("cost_center");
                return {
                    filters: {
                        cost_center: cost_center
                    }
                };
            }
        },
        {
            "fieldname": "report_type",
            "label": __("Report Type"),
            "fieldtype": "Select",
            "options": "\nLabour Cost Details\nMachinery and Equipment\nMaterial Consumption\nExpenditure of Project Implementation Unit\nExpenditure for Mess\nHSD Issued Details",
            // "reqd": 1
        },
        {
            "fieldname": "date",
            "label": __("Date"),
            "fieldtype": "Date",
            default: frappe.datetime.nowdate(),
        },
        {
            "fieldname": "show_overall",
            "fieldtype": "Check",
            "label": __("Show Overall"),
            "default": 0,
        },
    ],

    onload: function(report) {
        // Hide the Report Type field when 'Show Overall' is checked
        report.get_filter('show_overall').get_value() ? report.get_filter('report_type').toggle(false) : report.get_filter('report_type').toggle(true);

        // Watch for changes in 'Show Overall' checkbox
        report.get_filter('show_overall').$input.on('change', function() {
            if (report.get_filter('show_overall').get_value()) {
                report.get_filter('report_type').toggle(false); // Hide Report Type field
            } else {
                report.get_filter('report_type').toggle(true); // Show Report Type field
            }
        });
    }
};
