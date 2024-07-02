// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Mess Advance', {
	// onload: function(frm) {
	// 	calculate_total_advance(frm);
	// },
	
	refresh: function(frm) {
		calculate_total_advance(frm);
	},

	training_center: function (frm) {
		frappe.call({
			method: "set_advance_party",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("paid_to")
			}
		});
	},

	month: function (frm) {
		frappe.call({
			method: "set_dates",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("from_date")
				frm.refresh_field("to_date")
			}
		});
	},
});

var calculate_total_advance = function(frm) {
	let total_amt = 0
	$.each(frm.doc['items'] || [], function(i, amt){
		total_amt += amt.amount;
	})
	frm.set_value('total_advance', total_amt);
	refresh_field('total_advance');
}
