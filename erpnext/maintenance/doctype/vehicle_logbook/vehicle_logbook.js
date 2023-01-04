// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("cost_center", "branch", "branch")
frappe.ui.form.on('Vehicle Logbook', {
	refresh: function (frm) {
		total_ro = 1
		to_ro = 0
		if (frm.doc.docstatus == 1) {
			total_ro = 0
			to_ro = 1
		}
		cur_frm.set_df_property("total_work_time", "read_only", total_ro);
		cur_frm.set_df_property("distance_km", "read_only", total_ro);
		cur_frm.set_df_property("final_hour", "read_only", to_ro);
		cur_frm.set_df_property("final_km", "read_only", to_ro);
	},
	vehicle_request: function (frm) {
		if (frm.doc.vehicle_request) {
			frappe.call({
				"method": "erpnext.maintenance.doctype.vehicle_logbook.vehicle_logbook.get_vehicle_request_details",
				args: { "vehicle_request": frm.doc.vehicle_request },
				callback: function (r) {
					if (r.message) {
						cur_frm.set_value("from_date", r.message[0][0]);
						cur_frm.set_value("to_date", r.message[0][1]);
						cur_frm.set_value("equipment", r.message[0][2]);
						cur_frm.set_value("equipment_type", r.message[0][3]);
						cur_frm.set_value("branch", r.message[0][4]);
						cur_frm.refresh_fields()

						frappe.model.get_value("Equipment", { 'name': r.message[0][2] }, "equipment_number", function (d) {
							cur_frm.set_value("registration_number", d.equipment_number);
						})
						frappe.call({
							"method": "erpnext.maintenance.doctype.vehicle_logbook.vehicle_logbook.get_equipment_hiring_form",
							args: {
								"equipment": frm.doc.equipment,
								"from_date": frm.doc.from_date,
								"to_date": frm.doc.to_date
							},
							callback: function (data) {
								if (data.message) {
									cur_frm.set_value("equipment_hiring_form", data.message[0][0]);
								}
								cur_frm.refresh_fields()
							}
						});
					}
				}
			});
		}
	},

	branch: function (frm) {
		if (frm.doc.branch) {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Cost Center',
					filters: {
						'branch': frm.doc.branch
					},
					fieldname: ['name']
				},
				callback: function (r) {
					if (r.message) {
						cur_frm.set_value("cost_center", r.message.name);
						refresh_field('cost_center');
					}
				}
			});
		}
	},
	"final_km": function (frm) {
		if (!frm.doc.docstatus == 1) {
			calculate_distance_km(frm)
		}
	},
	"initial_km": function (frm) {
		calculate_distance_km(frm)
	},
	"total_work_time": function (frm) {
		if (frm.doc.docstatus == 1) {
			calculate_work_hour(frm)
			cur_frm.refresh_fields()
		}
		if (frm.doc.total_work_time && frm.doc.ys_hours && frm.doc.include_hour) {
			cur_frm.set_value("consumption_hours", frm.doc.total_work_time * frm.doc.ys_hours)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	},
	"distance_km": function (frm) {
		if (frm.doc.docstatus == 1) {
			calculate_distance_km(frm)
			cur_frm.refresh_fields()
		}
		if (frm.doc.distance_km && frm.doc.ys_km && frm.doc.include_km) {
			cur_frm.set_value("consumption_km", frm.doc.distance_km / frm.doc.ys_km)
			cur_frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
			cur_frm.refresh_fields()
		}
	},


	// opening_balance: function (frm) {
	// 	calculate_closing(frm)
	// },

	// hsd_received: function (frm) {
	// 	calculate_closing(frm)
	// },

	// consumption_hours: function (frm) {
	// 	if (frm.doc.total_work_time && frm.doc.ys_hours && frm.doc.include_hour) {
	// 		frm.set_value("consumption", flt(frm.doc.other_consumption) + flt(frm.doc.consumption_km) + flt(frm.doc.consumption_hours))
	// 		cur_frm.refresh_field("consumption")
	// 		calculate_closing(frm)
	// 	}
	// },

	// consumption: function (frm) {
	// 	calculate_closing(frm)
	// }
});

// function calculate_closing(frm) {
// 	frm.set_value("closing_balance", frm.doc.hsd_received + frm.doc.opening_balance - frm.doc.consumption)
// 	cur_frm.refresh_field("closing_balance")
// }

function calculate_distance_km(frm) {
	if (frm.doc.docstatus == 0) {
		if (flt(frm.doc.final_km) > flt(frm.doc.initial_km)) {
			cur_frm.set_value("distance_km", flt(frm.doc.final_km) - flt(frm.doc.initial_km))
			frm.refresh_fields()
		}
		else {
			cur_frm.set_value("distance_km", "0")
			frm.refresh_fields()
			if (frm.doc.final_km) {
				frappe.msgprint("Final KM should be greater than Initial KM")
			}
		}
	}
	if (frm.doc.docstatus == 1) {
		cur_frm.set_value("final_km", flt(frm.doc.distance_km) + flt(frm.doc.initial_km))
		cur_frm.refresh_fields()
	}
}

// function calculate_work_hour(frm) {
// 	if (frm.doc.docstatus == 0) {
// 		if (flt(frm.doc.final_hour) > flt(frm.doc.initial_hour)) {
// 			cur_frm.set_value("total_work_time", flt(frm.doc.final_hour) - flt(frm.doc.initial_hour))
// 			frm.refresh_fields()
// 		}
// 		else {
// 			cur_frm.set_value("total_work_time", "0")
// 			frm.refresh_fields()
// 			if (frm.doc.final_hour) {
// 				frappe.msgprint("Final Hour should be greater than Initial Hour")
// 			}
// 		}
// 	}
// 	if (frm.doc.docstatus == 1) {
// 		cur_frm.set_value("final_hour", flt(frm.doc.total_work_time) + flt(frm.doc.initial_hour))
// 		cur_frm.refresh_fields()
// 	}
// }


cur_frm.add_fetch("equipment", "equipment_number", "equipment_number")
cur_frm.add_fetch("equipment", "hsd_type", "pol_type")
cur_frm.add_fetch("equipment", "current_operator", "equipment_operator")
cur_frm.add_fetch("operator", "employee_name", "driver_name")

//Vehicle Log Item  Details
frappe.ui.form.on("Vehicle Log", {
	"from_time": function (frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"to_time": function (frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"from_km_reading": function (frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"to_km_reading": function (frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	"idle_time": function (frm, cdt, cdn) {
		total_time(frm, cdt, cdn)
	},
	"work_time": function (frm, cdt, cdn) {
		total_time(frm, cdt, cdn)
	},
	"initial_km": function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		if (item.final_km) {
			item.total_km_run = item.final_km - item.initial_km
		}
		if (item.total_km_run < 0) {
			frappe.throw("Initial km cannot be greater than final km")
		}
		frm.refresh_fields()
	},
	"final_km": function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		item.total_km_run = item.final_km - item.initial_km
		frm.refresh_fields()
		if (item.total_km_run < 0) {
			frappe.throw("Initial km cannot be greater than final km")
		}
	}
})

function get_openings(equipment, from_date, to_date, pol_type) {
	if (equipment && from_date && to_date && pol_type) {
		frappe.call({
			"method": "erpnext.maintenance.doctype.vehicle_logbook.vehicle_logbook.get_opening",
			args: { "equipment": equipment, "from_date": from_date, "to_date": to_date, "pol_type": pol_type },
			callback: function (r) {
				if (r.message) {
					cur_frm.set_value("opening_balance", r.message[0])
					cur_frm.set_value("hsd_received", r.message[3])
					cur_frm.set_value("initial_km", r.message[1])
					cur_frm.set_value("initial_hour", r.message[2])
					cur_frm.refresh_fields()
				}
			}
		})
	}
}

function total_time(frm, cdt, cdn) {
	var total_idle = total_work = 0;
	frm.doc.vlogs.forEach(function (d) {
		if (d.idle_time) {
			total_idle += d.idle_time
		}
		if (d.work_time) {
			total_work += d.work_time
		}
	})
	frm.set_value("total_idle_time", total_idle)
	frm.set_value("total_work_time", total_work)
	cur_frm.refresh_field("total_work_time")
	cur_frm.refresh_field("total_idle_time")
}

function calculate_time(frm, cdt, cdn) {
	var item = locals[cdt][cdn]
	// if (item.from_time && item.to_time && item.to_time >= item.from_time) {
	// 	frappe.model.set_value(cdt, cdn, "time", frappe.datetime.get_hour_diff(Date.parse("2/12/2016" + ' ' + item.to_time), Date.parse("2/12/2016" + ' ' + item.from_time)))
	// }
	cur_frm.refresh_field("time")
}

function calculate_distance(frm, cdt, cdn) {
	var item = locals[cdt][cdn]
	if (item.from_km_reading && item.to_km_reading && item.to_km_reading >= item.from_km_reading) {
		frappe.model.set_value(cdt, cdn, "distance", item.to_km_reading - item.from_km_reading)
	}
	cur_frm.refresh_field("distance")
}

frappe.ui.form.on("Vehicle Logbook", "refresh", function (frm) {
	cur_frm.set_query("equipment", function () {
		return {
			"filters": {
				"equipment_type": frm.doc.equipment_type
			}
		};
	});

    /*cur_frm.set_query("equipment", function() {
        return {
	    query: "erpnext.maintenance.doctype.equipment.equipment.get_equipments",
            "filters": {
                "ehf_name": frm.doc.ehf_name,
            }
        };
    });
    */

});

frappe.ui.form.on("Vehicle Logbook",{
	refresh: function(frm){
		if (frm.doc.docstatus == 1){
			frm.add_custom_button("Make Hire Charge Invoice", function(){
				frappe.model.open_mapped_doc({
					method: "erpnext.maintenance.doctype.vehicle_logbook.vehicle_logbook.prepare_hire_charge_invoice",
					frm: cur_frm
				})
			});
		}
	}
});