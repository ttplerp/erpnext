// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Equipment Engagement', {
	onload: function (frm) {
		let grid = frm.fields_dict['items'].grid;
		grid.cannot_add_rows = true;
	},

	refresh: function(frm) {
		if (frm.doc.docstatus != 1 && !frm.is_new()) {
			frm.add_custom_button(__("Get Equipment"), function () {
				frm.events.get_equipment_details(frm);
			}).toggleClass("btn-primary", !(frm.doc.items || []).length);
		}

		frm.set_query("project", function(doc){
			return {
				filters: {
					'status': "Open",
					'branch': doc.branch,
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
	},

	get_equipment_details: function (frm) {
		return frappe
			.call({
				doc: frm.doc,
				method: "fill_equipment_details",
				freeze: true,
				freeze_message: __("Fetching Equipment"),
			})
			.then((r) => {
				if (r.docs?.[0]?.items) {
					frm.dirty();
					frm.save();
				}

				frm.refresh();
				frm.scroll_to_field("items");
			});
	},
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

