// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["POL Receive Report"] = {
	"filters": [
		{
			"fieldname":"branch",
			"label": ("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": "100",
			"reqd": 1
		},
		{
			"fieldname":"equipment",
			"label": ("Equipment"),
			"fieldtype": "Link",
			"options": "Equipment",
			"width": "100",
			"on_change": function(query_report) {
				var equip = query_report.get_values().equipment;
				frappe.query_report.set_filter_value('equipment_no', "")
				
				if (!equip) {
					return;
				}
				frappe.db.get_value("Equipment", equip, "equipment_number", function(value) {
					frappe.query_report.set_filter_value('equipment_no', value["equipment_number"]);
				});
				if (query_report.get_values().branch && query_report.get_values().equipment){
					frappe.call({
						method:'erpnext.maintenance.report.pol_receive_report.pol_receive_report.get_previous_km',
						args:{
							'from_date':query_report.get_values().from_date,
							'branch':query_report.get_values().branch,
							'equipment':query_report.get_values().equipment,
							},
						callback: function(r) {
							if (r.message) {
								frappe.query_report.set_filter_value("prev_km_reading", r.message);
							}else{
								frappe.query_report.set_filter_value("prev_km_reading",0);
							}
						}
					});
				}
			},
			"reqd": 1,
		},
		{
			"fieldname":"equipment_no",
			"label": __("Equipment Number"),
			"fieldtype": "Data",
			"read_only": 1,
		},
		{
			"fieldname":"from_date",
			"label": ("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default":frappe.datetime.month_start(),
			"on_change":function(query_report){
				if (query_report.get_values().branch && query_report.get_values().equipment){
					frappe.call({
						method:'erpnext.maintenance.report.pol_receive_report.pol_receive_report.get_previous_km',
						args:{
							'from_date':query_report.get_values().from_date,
							'branch':query_report.get_values().branch,
							'equipment':query_report.get_values().equipment,
							},
						callback: function(r) {
							if (r.message) {
								frappe.query_report.set_filter_value("prev_km_reading", r.message);
							} else{
								frappe.query_report.set_filter_value("prev_km_reading",0);
							}
						}
					});
				}
			}
		},
		{
			"fieldname":"to_date",
			"label": ("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default":frappe.datetime.month_end()
		},
		{
			'fieldname':'prev_km_reading',
			'fieldtype':'Float',
			'label':'Previous KM Reading',
			'read_only':1
			// 'hidden':1
		}
	]
}
