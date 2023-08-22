// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Logbook', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1 ){
			cur_frm.add_custom_button(__('Create Hire Charge Invoice'), function() {
					frm.events.make_hire_charge_invoice(frm)
				}, __("Create"));
		};
	},
	// onload: function (frm) { 
	// 	project = frappe.db.get_value("Project",{'branch':doc.frm.branch})
	// },
	branch:function(frm){		
		frm.set_query("equipment_hiring_form", function () {
			return {
				filters: {
					branch: frm.doc.branch,
					disabled: 0,
					docstatus: 1
				}
			}
		});
		frm.set_query("project", function () {
			return {
				filters: {
					branch: frm.doc.branch
				}
			}
		});
		return frappe.call({
			method: "get_project",
			doc: frm.doc,
			callback: function (r) {
				frm.set_value("project", r.message);
				frm.refresh_fields();
			}
		});
		
	},
	make_hire_charge_invoice:function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.production.doctype.logbook.logbook.make_hire_charge_invoice",
			frm: cur_frm,
			doc: frm
		})
	}
});

frappe.ui.form.on("Logbook Item", {
	initial_hour: function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	final_hour: function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	initial_km: function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	final_km: function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
	idle_time: function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn)
	},
})

var calculate_time = function(frm, cdt, cdn) {
	let hour = 0
	let km = 0
	let item = locals[cdt][cdn]
	hour = item.final_hour - item.initial_hour - item.idle_time
	km = item.final_km - item.initial_km
	frappe.model.set_value(cdt, cdn,"hours", hour)
	frappe.model.set_value(cdt, cdn,"total_km", km)

	frm.refresh_fields("items")
}