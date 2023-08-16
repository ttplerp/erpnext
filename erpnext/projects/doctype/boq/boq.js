// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('BOQ', {
	setup: function (frm) {},

	refresh: function (frm) {
		// cur_frm.set_df_property("boq_item", "read_only",  frm.doc.docstatus == 1);

		if (!frm.doc.__islocal && frm.doc.docstatus == 1) {
			if (frappe.model.can_read("BOQ Adjustment")) {
				frm.add_custom_button(__("Adjustments"), function () {
					frappe.route_options = { "boq": frm.doc.name }
					frappe.set_route("List", "BOQ Adjustment");
				}, __("View"), true);
			}
			if (frappe.model.can_read("BOQ Substitution")) {
				frm.add_custom_button(__("Substitutions"), function () {
					frappe.route_options = { "boq": frm.doc.name }
					frappe.set_route("List", "BOQ Substitution");
				}, __("View"), true);
			}

			// if (frappe.model.can_read("BOQ Addition")) {
			// 					frm.add_custom_button(__("Additions"), function () {
			// 							frappe.route_options = { "boq": frm.doc.name }
			// 							frappe.set_route("List", "BOQ Addition");
			// 					}, __("View"), true);
			// 			}

			if (frappe.model.can_read("MB Entry")) {
				frm.add_custom_button(__("MB Entries"), function () {
					frappe.route_options = { "boq": frm.doc.name }
					frappe.set_route("List", "MB Entry");
				}, __("View"), true);
			}

			if (frappe.model.can_read("Project Invoice")) {
				frm.add_custom_button(__("Invoices"), function () {
					frappe.route_options = { "boq": frm.doc.name }
					frappe.set_route("List", "Project Invoice");
				}, __("View"), true);
			}

		}

		frm.trigger("get_defaults");

		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__("BOQ Adjustment"), function () { frm.trigger("make_boq_adjustment") },
				__("Make"), "icon-file-alt"
			);			
			frm.add_custom_button(__("BOQ Substitution"), function () { frm.trigger("make_boq_substitution") },
				__("Make"), "icon-file-alt"
			);
			frm.add_custom_button(__("BOQ Addition"), function () { frm.trigger("make_additional_boq") },
				__("Make"), "icon-file-alt"
			);
			
			if (frm.doc.party_type !== "Supplier") {
				frm.add_custom_button(__("Subcontract"), function () { frm.trigger("make_boq_subcontract") }, __("Make"), "icon-file-alt");
			}
		}

		if (frm.doc.docstatus == 1 && parseFloat(frm.doc.claimed_amount) < (parseFloat(frm.doc.total_amount) + parseFloat(frm.doc.price_adjustment))) {
			frm.add_custom_button(__("Measurement Book Entry"), function () { frm.trigger("make_book_entry") },
				__("Make"), "icon-file-alt"
			);
			frm.add_custom_button(__("Project Invoice"), function () { frm.trigger("make_mb_invoice") },
				__("Make"), "icon-file-alt"
			);
		}
        frm.set_query("boq_code", "boq_item", function () {
            return {
                filters: {
                    is_service_item:1,
                    disabled:0
                }
            };
        });
	},
	make_boq_adjustment: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.boq.boq.make_boq_adjustment",
			frm: frm
		});
	},

	make_boq_substitution: function (frm) {
        frappe.model.open_mapped_doc({
            method: "erpnext.projects.doctype.boq.boq.make_boq_substitution",
            frm: frm
        });
	},

	make_additional_boq: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.boq.boq.make_additional_boq",
			frm: frm
		});
	},
	//Logic Ends
	make_direct_invoice: function (frm) {
		frappe.model.open_mapped_doc({
			method: "make_direct_invoice",
			frm: frm
		});
	},

	make_boq_subcontract: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.boq.boq.make_boq_subcontract",
			frm: frm
		});
	},

	make_mb_invoice: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.boq.boq.make_mb_invoice",
			frm: frm
		});
	},

	make_book_entry: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.boq.boq.make_book_entry",
			frm: frm
		});
	},

	project: function (frm) {
		frm.trigger("get_defaults");
	},

	make_boq_advance: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.boq.boq.make_boq_advance",
			frm: frm
		});
	},
});

frappe.ui.form.on("BOQ Item", {
	quantity: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},

	rate: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},

	amount: function (frm) {
		calculate_total_amount(frm);
	},
	no: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
		frm.refresh_field("quantity", cdt, cdn)
	},
	breath: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
		frm.refresh_field("quantity", cdt, cdn)
	},
	height: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
		frm.refresh_field("quantity", cdt, cdn)
	},
	length: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
		frm.refresh_field("quantity", cdt, cdn)
	},
	coefficient: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		let quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
		frm.refresh_field("quantity", cdt, cdn)
	}
})

var calculate_amount = function (frm, cdt, cdn) {
	let child = locals[cdt][cdn];
	let amount = 0.0;

	amount = parseFloat(child.quantity) * parseFloat(child.rate)

	frappe.model.set_value(cdt, cdn, 'amount', parseFloat(amount));
	frappe.model.set_value(cdt, cdn, 'balance_quantity', parseFloat(child.quantity));
	frappe.model.set_value(cdt, cdn, 'balance_amount', parseFloat(amount));
}

var calculate_total_amount = function (frm) {
	let bi = frm.doc.boq_item || [];
	let total_amount = 0.0, balance_amount = 0.0;

	for (let i = 0; i < bi.length; i++) {
		if (bi[i].amount) {
			total_amount += parseFloat(bi[i].amount);
		}
	}
	balance_amount = parseFloat(total_amount) - parseFloat(frm.doc.received_amount)
	cur_frm.set_value("total_amount", total_amount);
	cur_frm.set_value("balance_amount", balance_amount);
}

