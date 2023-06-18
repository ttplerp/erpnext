// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maintenance Application Form', {
	refresh: function(frm) {
		if (!frm.doc.technical_sanction && frm.doc.docstatus == 1) {
			frm.add_custom_button("Create Technical Sanction", function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.rental_management.doctype.maintenance_application_form.maintenance_application_form.make_technical_sanction",
					frm: cur_frm
				});
			});
		}
	},
	setup: function(frm) {
		frm.set_query("tenant", function(){
			return {
				filters: [
					["status", "=", "Allocated"]
				]
			}
		});
		frm.set_query("block_no", function(){
			return {
				filters: [
					["location", "=", frm.doc.location]
				]
			}
		});
		frm.set_query("flat_no", function(){
			return {
				filters: [
					["block_no", "=", frm.doc.block_no],
					["status", "not in", ["Allocated", "Under Maintenance"]]
				]
			}
		});
	},
	no_current_tenant: function(frm) {
		if(frm.doc.no_current_tenant == 1){
			frm.set_value("tenant", "");
		}
	}
});
