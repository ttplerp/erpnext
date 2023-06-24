// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Equipment Hiring Form', {
	refresh: function(frm) {
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
	
	make_logbook:function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.fleet_management.doctype.equipment_hiring_form.equipment_hiring_form.make_logbook",
			frm: frm
		})
	},
	party_type: function(frm){
		if (frm.doc.party_type == "Supplier"){
			frm.set_value("is_hired", 1)
		}else{
			frm.set_value("is_hired", 0)
		}
	},

	is_hired: function(frm){
		if (frm.doc.is_hired === 1){
			frm.set_query("equipment", function() {
				return {
					filters: {
						hired_equipment: 1,
						branch: frm.doc.branch,
						supplier: frm.doc.party
					}
				}
			})
		}else{
			frm.set_query("equipment", function() {
				return {
					filters: {
						hired_equipment: 0,
						branch: frm.doc.branch
					}
				}
			})
		}
	},
	is_internal: function(frm){
		if (frm.doc.party_type == "Customer"){
			if (frm.doc.is_internal == 1){
				frm.set_query("party", function() {
					return {
						"filters": {
							"customer_group": "Internal",
							"disabled": 0
						}
					}
				})
			}else{
				frm.set_query("party", function() {
					return {
						"filters": {
							"disabled": 0
						}
					}
				})
			}
		}
	},
	party: function(frm){
		frappe.call({
			method: 'set_internal_cc_and_branch',
			doc: frm.doc,
			callback:  () =>{
				frm.refresh_field("party_branch")
				frm.refresh_field("party_cost_center")
			}
		})
	}
});

frappe.ui.form.on('EHF Rate', {
	"rate_type": function(frm, cdt, cdn) {
		get_rates(frm, cdt, cdn)
	},
	"from_date": function(frm, cdt, cdn){
		get_rates(frm, cdt, cdn)
	}
});

function get_rates(frm, cdt, cdn) {
	var item = locals[cdt][cdn]
	if (frm.doc.equipment_model && frm.doc.equipment_type && item.rate_type && item.from_date) {
		return frappe.call({
			method: "get_hire_rates",
			doc: frm.doc,
			args: {"from_date": item.from_date},
			callback: function(r) {
				if(r.message) {
					if(item.rate_type == "Without Fuel") {
						frappe.model.set_value(cdt, cdn, "hiring_rate", r.message[0].without_fuel)
					}
					else if (item.rate_type == "With Fuel") {
						frappe.model.set_value(cdt, cdn, "hiring_rate", r.message[0].with_fuel)
					}
					else if(item.rate_type == "Cft - Broadleaf") {
						frappe.model.set_value(cdt, cdn, "hiring_rate", r.message[0].cft_rate_bf)
					}
					else if(item.rate_type == "Cft - Conifer") {
						frappe.model.set_value(cdt, cdn, "hiring_rate", r.message[0].cft_rate_co)
					}
					frappe.model.set_value(cdt, cdn, "idle_rate", r.message[0].idle)
				}				
				frm.refresh_fields("ehf_rate")
			}
		})	
	}
}