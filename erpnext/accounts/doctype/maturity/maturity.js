// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maturity', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {

			if (frappe.model.can_read("Journal Entry")) {
				cur_frm.add_custom_button('Journal Entries', function () {
					frappe.route_options = {
						"Journal Entry Account.reference_type": "Treasury",
						"Journal Entry Account.reference_name": frm.doc.treasury_id,
					};
					frappe.set_route("List", "Journal Entry");
				}, __("View"));
			}
		}
	},
	posting_date: function(frm){
		if(frm.doc.posting_date){
			frappe.call({
				method: "get_days",
				doc: frm.doc,
				callback: function(r){
					if(r.message){
						frm.set_value("days", r.message)
					}
					frm.refresh_field("days");
				}
			})
		}
	}
});
