// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Technical Sanction Bill', {
	refresh: function(frm) {
		// if (frm.doc.docstatus == 1 && !frm.doc.maintenance_payment) {
		// 	frm.add_custom_button("Make Payment", function () {
		// 		frappe.model.open_mapped_doc({
		// 			method: "erpnext.rental_management.doctype.technical_sanction_bill.technical_sanction_bill.make_payment",
		// 			frm: cur_frm
		// 		});
		// 	});
		// }
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}

		frm.add_custom_button(
			__("Journal Entry"),
			function () {
				frappe.route_options = {
				name: frm.doc.journal_entry
				};
				frappe.set_route("List", "Journal Entry");
			},
			__("View")
		);

		if (frm.doc.docstatus == 1 && !frm.doc.journal_entry) {
			frm.add_custom_button(
				__("Make Payment"),
				function () {
					frappe.call({
						method: "make_journal_entry",
						doc: frm.doc,
						callback: function(r){
							frm.refresh();
						}
					});	
				},
				__("Make Payment")
			);
		}

	},
	"deduction": function (frm) {
		console.log("hello world")
		calculate_total_amount(frm)
	},
	"get_advances": function (frm) {
		if (frm.doc.technical_sanction && frm.doc.party_type && frm.doc.party) {
			frappe.call({
				method: "erpnext.rental_management.doctype.technical_sanction_bill.technical_sanction_bill.get_advance_list",
				args: {
					"technical_sanction": frm.doc.technical_sanction,
					"party_type": frm.doc.party_type,
					"party": frm.doc.party
				},
				callback: function (r) {
					if (r.message) {
						cur_frm.clear_table("advance");
						r.message.forEach(function (adv) {
							var row = frappe.model.add_child(frm.doc, "Technical Sanction Bill Advance", "advance");
							row.reference_doctype = "Technical Sanction Advance";
							row.reference_name = adv['name'];
							row.total_amount = flt(adv['balance_amount']);
							row.allocated_amount = 0.00;
						});
						frm.refresh_field("advance");
					}
					else {
						cur_frm.clear_table("advance");
						cur_frm.refresh();
					}
				}
			});
		}
		else {
			frappe.throw("Either party type or party are missing in the technical sanction!")
		}
	},
	"tax_withholding_category": function (frm) {

		if (!frm.doc.tax_withholding_category) {
			cur_frm.set_df_property("tds_account", "reqd", (frm.doc.tax_withholding_category)? 1:0);
			cur_frm.set_value("tds_account", "");
			cur_frm.set_value("tds_amount", 0.0);
			return
		}
		calculate_tds(frm);
		
		cur_frm.set_df_property("tds_account", "reqd", (frm.doc.tax_withholding_category)? 1:0);
	},
	"tds_amount": function (frm) {
		calculate_total_amount(frm)
	}
});

frappe.ui.form.on('Technical Sanction Item', {
	"qty": function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "total", row.amount * row.qty);
		var total = 0;
		for (var i in cur_frm.doc.items) {
			var item = cur_frm.doc.items[i];
			total += item.total;
		}
		cur_frm.set_value("total_gross_amount", total);
		cur_frm.set_value("tds_taxable_amount", total);
	}
});

frappe.ui.form.on('Technical Sanction Deduction', {
	"deduction_amount": function (frm, cdt, cdn) {
		calculate_total_amount(frm)
	},
	deduction_remove: function (frm) {
		calculate_total_amount(frm)
	},
})
frappe.ui.form.on('Technical Sanction Bill Advance', {
	"allocated_amount": function (frm, cdt, cdn) {
		console.log("hello world")
		calculate_total_amount(frm)
	},
})

function calculate_total_amount(frm) {
	frappe.call({
		method: "calculate_total_amount",
		arg: {},
		callback: function (r, rt) { frm.refresh_fields() },
		doc: frm.doc,
	});
}

function calculate_tds(frm) {
	frappe.call({
		method: "get_tds_details",
		doc: frm.doc,
		args: {
			tax_withholding_category: frm.doc.tax_withholding_category
		},
		callback: function(r) {
			if(r.message) {
				frm.set_value("tds_account", r.message.tax_withholding_account);
				cur_frm.refresh_field("tds_account");
				frm.set_value("tds_amount", flt(flt(r.message.tax_withholding_rate * frm.doc.tds_taxable_amount) / 100, 2) ?? 0.0);
			}
		}
	})
}