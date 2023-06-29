// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["General Tenant Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		},
		{
			fieldname: "rental_official",
			label: __("Rental Focal"),
			fieldtype: "Link",
			width: "80",
			options: "Employee",
			get_query: function() {
				return {
					filters: [
						['Employee', 'user_id', 'in', ['dema@nhdcl.bt','bumpa.dema@nhdcl.bt','dm.ghalley@nhdcl.bt','rinzin.dema@nhdcl.bt','dorji.wangmo@nhdcl.bt']]
					]
				}
			},
			on_change: function(query_report) {
				var emp = query_report.get_filter_value('rental_official');
				if (!emp) {
					return;
				}
				frappe.db.get_value("Employee", emp, "employee_name", function(value) {
					frappe.query_report.set_filter_value('focal_name', value["employee_name"]);
				});
			}
		},
		{
			"fieldname": "focal_name",
			"label": __("Focal Name"),
			"fieldtype": "Data",
			"read_only": 1
		}
	]
};
