// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Mess Advance', {
	onload: function(frm) {
		frm.set_query('branch', function(doc) {
			return {
				filters: {
					"company": frm.doc.company,
				}
			}
		});
		frm.set_query('training_management', function(doc) {
			return {
				filters: {
					"company": frm.doc.company,
					"status": "On Going",
					"training_center": frm.doc.training_center,
				}
			}
		});

		frm.set_query('desuup_deployment_entry', function(doc) {
			return {
				filters: {
					"company": frm.doc.company,
					"status": "On Going",
				}
			}
		});
	},
	
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

	get_desuups: function (frm) {
		frm.set_value("number_of_desuups", 0);
		frm.refresh_field("number_of_desuups");
		return frappe.call({
			doc: frm.doc,
			method: 'get_desuup_details',
			callback: function(r) {
				if (r.message){
					frm.set_value("number_of_desuups", r.message);
					frm.refresh_field("number_of_desuups");
					frm.refresh_field("items");
					frm.dirty();
				}
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching Desuup Records...</span>'
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
