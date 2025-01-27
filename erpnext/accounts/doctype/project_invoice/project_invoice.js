// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Invoice', {
	onload: function (frm, cdt, cdn) {
		if (frm.doc.project && frm.doc.__islocal) {
			if (frm.doc.docstatus != 1) {
				get_mb_list(frm);
				calculate_totals(frm);
			}
		}

		frm.set_query("party_type", function () {
			return {
				query: "erpnext.accounts.doctype.project_invoice.project_invoice.get_project_party_type",
				filters: {
					project: frm.doc.project
				}
			};
		});

		frm.set_query("party", function () {
			return {
				query: "erpnext.accounts.doctype.project_invoice.project_invoice.get_project_party",
				filters: {
					project: frm.doc.project,
					party_type: frm.doc.party_type
				}
			};
		});

		frm.set_query("account", "deductions", function (doc) {
			return {
				filters: {
					'is_group': 0,
				}
			}
		});
	},

	refresh: function (frm, cdt, cdn) {
		if (frm.doc.__islocal) {
			calculate_totals(frm);
		}

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.invoice_date,
					to_date: frm.doc.invoice_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));

            if (frm.doc.outstanding_amount > 0){
                cur_frm.add_custom_button(__('Pay'), function(doc) {
                    frm.events.make_payment_entry(frm)
                })
            }				
		}
	},
    make_payment_entry:function(frm){
		frappe.call({
			method:"erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
				party_type:frm.doc.party_type
			},
			callback: function (r) {
				var doc = frappe.model.sync(r.message);
				frappe.set_route("Form", doc[0].doctype, doc[0].name);
			},
		});
	},
	get_advances: function (frm) {
		get_advance_list(cur_frm)
	},
	project: function (frm) {
		get_mb_list(frm);
		calculate_totals(frm);
		cur_frm.set_value("party", "");
	},

    tds_percent:function(frm){
        if (frm.doc.tds_percent){
			frappe.call({
				method: "erpnext.accounts.utils.get_tds_account",
				args: {
					percent:frm.doc.tds_percent,
					company:frm.doc.company,
					party_type:frm.doc.party_type,
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("tds_account", r.message)
						frm.refresh_fields("tds_account")
					}
				}
			});
			tds_retention_calculation(frm);
		}
    },

	retention_percent:function(frm){
        if (frm.doc.retention_percent){
			frappe.call({
				method: "erpnext.accounts.utils.get_retention_account",
				args: {
					percent:frm.doc.retention_percent,
					company:frm.doc.company,
					party_type:frm.doc.party_type,
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("retention_account", r.message)
						frm.refresh_fields("retention_account")
					}
				}
			});
			tds_retention_calculation(frm);
		}
    },

	party_type: function (frm) {
		get_mb_list(frm);
		calculate_totals(frm);
		cur_frm.set_value("party", "");
	},

	party: function (frm) {
		get_mb_list(frm);
		
        if (frm.doc.party){
			frappe.call({
				method: "erpnext.accounts.party.get_party_account",
				args: {
					party_type:frm.doc.party_type,
					party:frm.doc.party,
					company: frm.doc.company,
					doctype: frm.doc.doctype,
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("debit_credit_account", r.message)
						frm.refresh_fields("debit_credit_account")
					}
				}
			});
		}
		calculate_totals(frm);

	},

	make_project_payment: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.project_payment.project_payment.make_project_payment",
			frm: frm
		});
	},

	// price_adjustment_percent: function (frm) {
	// 	calculate_totals(frm);
	// },

	price_adjustment_amount: function (frm) {
		calculate_totals(frm);
	},

	check_all: function (frm) {
		check_uncheck_all(frm);
	},

	check_all_mb: function (frm) {
		check_uncheck_all(frm);
	},

	get_mb_entries: function (frm, cdt, cdn) {
		get_mb_list(frm);
	},

});

frappe.ui.form.on("Project Invoice BOQ", {
	invoice_quantity: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];

		if (child.invoice_quantity > child.act_quantity) {
			msgprint(__("Invoice Quantity cannot be greater than balance quantity.").format(child.invoice_quantity))
		}

		frappe.model.set_value(cdt, cdn, 'invoice_amount', (parseFloat(child.invoice_quantity) * parseFloat(child.invoice_rate)).toFixed(2));
	},

	invoice_amount: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];

		if (child.invoice_amount > child.act_amount) {
			msgprint(__("Invoice Amount cannot be greater than balance amount."));
		}
		calculate_totals(frm);
	},

	is_selected: function (frm, cdt, cdn) {
		calculate_totals(frm);
	},

	project_invoice_boq_remove: function (frm, cdt, cdn) {
		calculate_totals(frm);
	},
});

frappe.ui.form.on("Project Invoice MB", {
	is_selected: function (frm, cdt, cdn) {
		calculate_totals(frm);
	},

	project_invoice_mb_remove: function (frm, cdt, cdn) {
		calculate_totals(frm);
	},

});

var get_mb_list = function (frm) {
	frappe.call({
		method: "get_mb_list",
		doc: frm.doc,
		callback: function (r) {
			cur_frm.refresh();
		}
	});
}

var calculate_totals = function (frm) {
	frappe.call({
		method: "calculate_totals",
		doc: frm.doc,
		callback: function (r) {
			frm.refresh_fields()
		},
		freeze: true,
		freeze_message: "Recalculating ..."
	})

	// var pi = frm.doc.project_invoice_boq || [];
	// var mb = frm.doc.project_invoice_mb || [];
	// var gross_invoice_amount = 0.0

	// if (frm.doc.docstatus != 1) {
		
	// 	for (var i = 0; i < mb.length; i++) {
	// 		if (mb[i].entry_amount && mb[i].is_selected == 1) {
	// 			gross_invoice_amount += flt(mb[i].entry_amount);
	// 		}
	// 	}

	// 	cur_frm.set_value("net_amount", ((gross_invoice_amount + frm.doc.price_adjustment_amount) - frm.doc.total_deduct_amount))
	// 	cur_frm.set_value("total_amount", (gross_invoice_amount + frm.doc.price_adjustment_amount));
	// }
}

var check_uncheck_all = function (frm) {
	var mb = frm.doc.project_invoice_mb || [];
	for (var id in mb) {
		frappe.model.set_value("Project Invoice MB", mb[id].name, "is_selected", frm.doc.check_all_mb);
	}
}

frappe.ui.form.on("Project Invoice Deduction", {
	amount: function (frm, cdt, cdn) {
		calculate_totals(frm, cdt, cdn);
	},

	deductions_remove: function (frm, cdt, cdn) {
		calculate_totals(frm, cdt, cdn);
	},

	deductions_add: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.cost_center);
	},
});

frappe.ui.form.on("Project Invoice Advance", {
	allocated_amount: function (frm) {
		calculate_totals(frm);
	},

	advances_remove: function (frm) {
		calculate_totals(frm);
	},
});

function get_advance_list(frm) {
	if (frm.doc.project && frm.doc.party_type && frm.doc.party) {
		frappe.call({
			method: "erpnext.accounts.doctype.project_invoice.project_invoice.get_advance_list",
			args: {
				"project": frm.doc.project,
				"party_type": frm.doc.party_type,
				"party": frm.doc.party
			},
			callback: function (r) {
				if (r.message) {
					cur_frm.clear_table("advances");
					r.message.forEach(function (adv) {
						console.log(adv['reference_doctype']);
						var row = frappe.model.add_child(frm.doc, "Project Invoice Advance", "advances");
						row.reference_doctype = adv['reference_doctype'];
						row.reference_name = adv['name'];
						row.total_amount = flt(adv['balance_amount']);
                        row.advance_account = adv['advance_account']
						row.allocated_amount = flt(adv['balance_amount']);
					});
					frm.refresh_field("advances");
				}
				else {
					cur_frm.clear_table("advances");
					cur_frm.refresh();
				}
                frm.dirty()
			}
		});
	} else {
		cur_frm.clear_table("advances");
		cur_frm.refresh();
	}
}

function tds_retention_calculation(frm) {
	cur_frm.set_value("tds_amount", (cur_frm.doc.tds_percent / 100) * cur_frm.doc.total_amount);
	cur_frm.set_value("retention_amount", (cur_frm.doc.retention_percent / 100) * cur_frm.doc.total_amount);
	cur_frm.refresh_field("tds_amount")
	cur_frm.refresh_field("retention_amount")
	calculate_totals(frm)
};
