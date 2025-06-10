// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Audit Report"] = {
	"filters": [
		{
			"fieldname": "audit_observation",
			"label": __("Audit Observation"),
			"fieldtype": "Link",
			"options": "Audit Observation"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.defaults.get_user_default("year_start_date"),
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"audit_type",
			"label": __("Audit Type"),
			"fieldtype": "Select",
			"options": "\nRegular Audit\nAd-hoc Audit",
			"width": "80",
			"default": ""
		},
		{
			"fieldname":"observation_type",
			"label": __("Observation Type"),
			"fieldtype": "Select",
			"options": "\nResolved\nFor Information\nFound in order\nUnresolved\nObservation\nUn-Reconciled",
			"width": "80",
			"default": ""
		},
	]
};
