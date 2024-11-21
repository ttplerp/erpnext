// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Equipment Engagement', {
	refresh: function(frm) {
		frm.set_query("project", function(doc){
			return {
				filters: {
					'status': "Open",
				}
			}
		});

		frm.set_query("equipment", "items", function(doc){
			return {
				filters: {
					'branch': doc.branch,
				}
			}
		});
	}
});

frappe.ui.form.on('Project Equipment Engagement Item', {
	hours: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let amount = child.hours * child.rate
		frappe.model.set_value(cdt, cdn, 'amount', parseFloat(amount));
		frm.refresh_field("amount", cdt, cdn)
	},
	rate: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let amount = child.hours * child.rate
		frappe.model.set_value(cdt, cdn, 'amount', parseFloat(amount));
		frm.refresh_field("amount", cdt, cdn)
	},
	amount: function(frm) {
		calculate_total_amount(frm)
	}
});

var calculate_total_amount = function (frm) {
	let d = frm.doc.items || [];
	let total_amount = 0.0;

	for (let i = 0; i < d.length; i++) {
		if (d[i].amount) {
			total_amount += parseFloat(d[i].amount);
		}
	}
	cur_frm.set_value("total_amount", total_amount);
}

