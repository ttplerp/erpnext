frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Completed Training"] = {
    method: "erpnext.training_and_skilling.dashboard_chart_source.completed_training.completed_training.get_data",
};