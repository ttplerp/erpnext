// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Vehicle Booking Status Report"] = {
	"filters": [
		{
			"fieldname":"branch",
			"fieldtype":"Link",
			"label":__("Branch"),
			"options":"Branch",
			"reqd":0
		},
		{
			"fieldname":"vehicle_type",
			"fieldtype":"Link",
			"label":__("Vehicle Type"),
			"options":"Equipment Type"
		},
		{
			"fieldname":"vehicle",
			"fieldtype":"Link",
			"label":__("Vehicle"),
			"options":"Equipment",
			"get_query": () => {
				var vehicle_type = frappe.query_report.get_filter_value('vehicle_type');
				if(vehicle_type){
					return {
						filters: {
							'equipment_type': vehicle_type
						}
					};
				}else{
					return {
						filters: [
							['Equipment', 'equipment_category', '=', 'Pool'],

						]
					};
				}
			}
		}
	]
};

