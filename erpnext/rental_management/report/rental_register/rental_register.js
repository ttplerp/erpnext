// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Rental Register"] = {
	"filters": [
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			default: frappe.defaults.get_user_default("fiscal_year"),
			reqd: 1,
		},
		{
			fieldname: "from_month",
			label: "From Month",
			fieldtype: "Select",
			options: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
			default: "01",
		},
		{
			fieldname: "to_month",
			label: "To Month",
			fieldtype: "Select",
			options: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
			default: "12",
		},
		{
			fieldname: "dzongkhag",
			label: "Dzongkhag",
			fieldtype: "Link",
			width: "80",
			options: "Dzongkhag",
		},
		{
			fieldname: "location",
			label: "Location ID",
			fieldtype: "Link",
			width: "80",
			options: "Locations",
		},
		{
			fieldname: "building_category",
			label: "Building Category",
			fieldtype: "Link",
			width: "80",
			options: "Building Category",
		},
		{
			fieldname: "ministry",
			label: "Ministry/Agency",
			fieldtype: "Link",
			width: "80",
			options: "Ministry and Agency",
		},
		{
			fieldname: "department",
			label: "Department ID",
			fieldtype: "Link",
			width: "80",
			options: "Tenant Department",
		},
		{
			fieldname: "town",
			label: "Town Category",
			fieldtype: "Link",
			width: "80",
			options: "Town Category",
		},
		{
			fieldname: "payment_mode",
			label: __("Payment Mode"),
			fieldtype: "Select",
			width: "80",
			options: ["", "Cash", "Cheque", "ePMS", "mBOB", "mPay", "TPay", "NHDCL Office"],
			default: "",
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
		},
		{
			fieldname: "building_classification",
			label: __("Building Classification"),
			fieldtype: "Link",
			width: "90",
			options: "Building Classification"
		},
		{
			fieldname: "status",
			label: "Status",
			fieldtype: "Select",
			width: "80",
			options: ["Draft", "Submitted"],
			reqd: 1,
			default: "Submitted",
		},
	]
};
