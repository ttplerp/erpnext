// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Maturity', {
	// refresh: function(frm) {

	// },
	posting_date: function(frm){
		frappe.call({
			method: "get_days",
			doc: frm.doc,
			callback: function(r){
				frm.refresh_field("days");
			}
		})
	}
});
