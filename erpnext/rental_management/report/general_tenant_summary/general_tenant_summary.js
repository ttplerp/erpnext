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
			label: __("Rental Official"),
			fieldtype: "Select",
			width: "80",
			options: ["", "Bumpa Dema", "Dik Maya Ghalley", "Rinzin Dema", "Seema Uroan", "Dorji Wangmo", "Sangay Dorji", "Sangay Dubjur", "Kunzang Choden", "Dema"],
		}
	]
};
