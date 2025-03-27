// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Desuup Monthly Attendance"] = {
    "filters": [
        {
            "fieldname": "year",
            "label": __("Year"),
            "fieldtype": "Select",
            "reqd": 1
        },
        {
            "fieldname": "month",
            "label": __("Month"),
            "fieldtype": "Select",
            "reqd": 1,
            "options": [
                { "value": 1, "label": __("Jan") },
                { "value": 2, "label": __("Feb") },
                { "value": 3, "label": __("Mar") },
                { "value": 4, "label": __("Apr") },
                { "value": 5, "label": __("May") },
                { "value": 6, "label": __("Jun") },
                { "value": 7, "label": __("Jul") },
                { "value": 8, "label": __("Aug") },
                { "value": 9, "label": __("Sep") },
                { "value": 10, "label": __("Oct") },
                { "value": 11, "label": __("Nov") },
                { "value": 12, "label": __("Dec") },
            ],
            "default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
        },
        {
            "fieldname": "report_for",
            "label": __("Report For"),
            "fieldtype": "Select",
            "options": [
                { "value": "1", "label": __("Trainee") },
                { "value": "2", "label": __("OJT") },
                { "value": "3", "label": __("Production") },
            ],
            "reqd": 1
        },
        {
            "fieldname": "ref_doc",
            "label": __("Reference Doc"),
            "fieldtype": "Dynamic Link",
            "options": ""
        },
        {
            "fieldname": "desuup",
            "label": __("Desuup"),
            "fieldtype": "Link",
            "options": "Desuup"
        }
    ],

    on_change: function (filter) {
        if (filter.fieldname === "report_for") {
            let refDocFilter = frappe.query_report.get_filter("ref_doc");

            // Set options based on report_for selection
            if (filter.value === "1") {
                refDocFilter.df.options = "Training Management";
            } else if (filter.value === "2" || filter.value === "3") {
                refDocFilter.df.options = "Desuup Deployment Entry";
            } else {
                refDocFilter.df.options = "";
            }

            refDocFilter.refresh();
        }
    },

    onload: function() {
        return frappe.call({
            method: "erpnext.training_and_skilling.report.desuup_monthly_attendance.desuup_monthly_attendance.get_attendance_years",
            callback: function(r) {
                if (r.message) {
                    let year_filter = frappe.query_report.get_filter('year');
                    year_filter.df.options = r.message;
                    year_filter.df.default = r.message.split("\n")[0];
                    year_filter.refresh();
                    year_filter.set_input(year_filter.df.default);
                }
            }
        });
    }
};