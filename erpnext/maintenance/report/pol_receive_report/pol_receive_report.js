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
				// frappe.query_report.set_filter_value('equipment_no', null)
				query_report.filters_by_name.equipment_no.set_input(null)
				query_report.trigger_refresh();
				if (!equip) {
					return;
				}
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
						doctype: 'Equipment',
						filters: {
							'name': equip
						},
						fieldname: ['equipment_number']
					},
					callback: function(r) {
						query_report.filters_by_name.equipment_no.set_input(r.message.equipment_number)
						query_report.trigger_refresh();
					}
				})
				frappe.call({
					method:'erpnext.maintenance.report.pol_receive_report.pol_receive_report.get_previous_km',
					args:{
						'from_date':query_report.get_values().from_date,
						'branch':query_report.get_values().branch,
						'equipment':query_report.get_values().equipment,
						'direct_consumption':query_report.get_values().direct
						},
					callback: function(r) {
						if (r.message)
							query_report.filters_by_name.prev_km_reading.set_input(r.message)
						else
							query_report.filters_by_name.prev_km_reading.set_input(0)
						query_report.trigger_refresh();
					}
				})
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
				if (query_report.get_values().branch){
					frappe.call({
						method:'erpnext.maintenance.report.pol_receive_report.pol_receive_report.get_previous_km',
						args:{
							'from_date':query_report.get_values().from_date,
							'branch':query_report.get_values().branch,
							'equipment':query_report.get_values().equipment,
							'direct_consumption':query_report.get_values().direct
							},
						callback: function(r) {
							// console.log(r.message)
							if (r.message)
								query_report.filters_by_name.prev_km_reading.set_input(r.message)
							else
								query_report.filters_by_name.prev_km_reading.set_input(0)
							query_report.trigger_refresh();
						}
					})
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
			"fieldname": "direct",
			"label": ("Show Only Direct Consumption"),
			"fieldtype": "Check",
			"default": 1,
			"on_change":function(query_report){
				frappe.call({
					method:'erpnext.maintenance.report.pol_receive_report.pol_receive_report.get_previous_km',
					args:{
						'from_date':query_report.get_values().from_date,
						'branch':query_report.get_values().branch,
						'equipment':query_report.get_values().equipment,
						'direct_consumption':query_report.get_values().direct
						},
					callback: function(r) {
						if (r.message)
							query_report.filters_by_name.prev_km_reading.set_input(r.message)
						else
							query_report.filters_by_name.prev_km_reading.set_input(0)
						query_report.trigger_refresh();
					}
				})
			}
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
