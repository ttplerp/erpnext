// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Equipment Hiring Form', {
	refresh: function(frm) {
		frm.set_query("party", function() {
			return {
				"filters": {
					"customer_group": "Internal"
				}
			}
		});

		if(frm.doc.docstatus == 1 ){
			cur_frm.add_custom_button(__('Logbooks'), function() {
				frappe.route_options = {
					"Logbook.equipment_hiring_form": me.frm.doc.name,
				};
				frappe.set_route("List", "Logbook");
			}, __("View"));
			if (frm.doc.disabled == 0){
				cur_frm.add_custom_button(__('Create Logbooks'), function() {
					frm.events.make_logbook(frm)
				}, __("Create"));
			}
		}
	},
	
	branch:function(frm){
		frm.set_query("equipment", function() {
			return {
				filters: {
					hired_equipment: 1,
					branch : frm.doc.branch
				}
			}
		})
	},

	make_logbook:function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.production.doctype.equipment_hiring_form.equipment_hiring_form.make_logbook",
			frm: cur_frm
		})
	},
	// party_type: function(frm){
	// 	frm.set_query("party", function() {
	// 		return {
	// 			"filters": {
	// 				"customer_group": "Internal"
	// 			}
	// 		}
	// 	});
	// },

	// is_internal: function(frm){
	// 	frm.set_query("party", function() {
	// 		return {
	// 			"filters": {
	// 				"customer_group": "Internal"
	// 			}
	// 		}
	// 	});
	// },

	// party: function(frm){
	// 	frm.set_query("party", function() {
	// 		return {
	// 			"filters": {
	// 				"branch": frm.doc.branch
	// 			}
	// 		}
	// 	});
	// }
});

frappe.ui.form.on('EHF Rate', {
	"rate_type": function(frm, cdt, cdn) {
		var child = locals[cdt][cdn]
		if (frm.doc.equipment && child.rate_type && child.from_date) {
			frappe.call({
				method: "erpnext.maintenance.doctype.equipment_hiring_form.equipment_hiring_form.get_hire_rates",
				args: {"e": doc.equipment, "from_date": doc.from_date},
				callback: function(r) {
					if(r.message) {
						if(r.message) {
							if(item.rate_type == "Without Fuel") {
								frappe.model.set_value(cdt, cdn, "rate", r.message[0].without_fuel)
							}
							else if (item.rate_type == "With Fuel") {
								frappe.model.set_value(cdt, cdn, "rate", r.message[0].with_fuel)
							}
							frappe.model.set_value(cdt, cdn, "idle_rate", r.message[0].idle)
						}				
						frm.refresh_fields("ehf_rate")
					}
				}
			})
		}
	},
})
