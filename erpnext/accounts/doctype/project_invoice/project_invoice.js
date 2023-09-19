// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('Project Invoice', {
	setup: function (frm) {
	},

	onload: function (frm, cdt, cdn) {
		toggle_child_tables(frm);
		if (frm.doc.project && frm.doc.__islocal) {
			if (frm.doc.docstatus != 1) {
				if (frm.doc.invoice_type == "Direct Invoice") {
					frm.trigger("boq_type");
				}
				else {
					get_mb_list(frm);
				}
				calculate_totals(frm);
			}
		}

		// party_type set_query
		frm.set_query("party_type", function () {
			return {
				query: "erpnext.accounts.doctype.project_invoice.project_invoice.get_project_party_type",
				filters: {
					project: frm.doc.project
				}
			};
		});

		// party set_query
		frm.set_query("party", function () {
			return {
				query: "erpnext.accounts.doctype.project_invoice.project_invoice.get_project_party",
				filters: {
					project: frm.doc.project,
					party_type: frm.doc.party_type
				}
			};
		});
	},

	refresh: function (frm, cdt, cdn) {
		frm.trigger("boq_type");
		frm.trigger("invoice_type");
		if (frm.doc.__islocal) {
			calculate_totals(frm);
		}

		if (frm.doc.docstatus === 1) {
			// if (frm.doc.payment_status != "Paid") {
				frappe.call({
					method: "erpnext.accounts.doctype.project_invoice.project_invoice.get_payment_entry",
					args: {
						doc_name: frm.doc.name,
						total_amount: frm.doc.net_invoice_amount,
						project: frm.doc.project,
						party: frm.doc.party,
						party_type: frm.doc.party_type
					},
					callback: function (r) {
						console.log(r.message)
						cur_frm.refresh_field("payment_status");

					},
				})
			// }
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.invoice_date,
					to_date: frm.doc_invoice_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));

            if (self.status != "Paid"){
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
		//cur_frm.add_fetch("project","customer","customer");

		if (frm.doc.invoice_type == "Direct Invoice") {
			frm.trigger("boq_type");
		}
		else {
			get_mb_list(frm);
		}
		calculate_totals(frm);
		cur_frm.set_value("party", "");
	},
    tds_rate:function(frm){
        if (frm.doc.tds_rate){
			frappe.call({
				method: "erpnext.accounts.utils.get_tds_account",
				args: {
					percent:frm.doc.tds_rate,
					company:frm.doc.company
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("tds_account",r.message)
						frm.refresh_fields("tds_account")
					}
				}
			});
		}
    },
	party_type: function (frm) {
		if (frm.doc.invoice_type == "Direct Invoice") {
			frm.trigger("boq_type");
		}
		else {
			get_mb_list(frm);
		}
		calculate_totals(frm);
		cur_frm.set_value("party", "");
	},

	party: function (frm) {
		if (frm.doc.invoice_type == "Direct Invoice") {
			frm.trigger("boq_type");
		}
		else {
			get_mb_list(frm);
		}
        if (frm.doc.party){
			frappe.call({
				method: "erpnext.accounts.party.get_party_account",
				args: {
					party_type:frm.doc.party_type,
					party:frm.doc.party,
					company: frm.doc.company,
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("debit_credit_account",r.message)
						frm.refresh_fields("debit_credit_account")
					}
				}
			});
		}
		calculate_totals(frm);

	},
	rebate_remove: function (frm) {
		calculate_totals(frm)
	},

	make_project_payment: function (frm) {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.project_payment.project_payment.make_project_payment",
			frm: frm
		});
	},

	price_adjustment_amount: function (frm) {
		calculate_totals(frm);
	},

	advance_recovery: function (frm) {
		calculate_totals(frm);
	},

	check_all: function (frm) {
		check_uncheck_all(frm);
	},

	check_all_mb: function (frm) {
		check_uncheck_all(frm);
	},

	boq_type: function (frm) {
		toggle_items_based_on_boq_type(frm);
	},

	invoice_type: function (frm) {
		frm.set_df_property("price_adjustment_amount", "read_only", (frm.doc.invoice_type === 'MB Based Invoice' ? 1 : 0));
	},

	get_mb_entries: function (frm, cdt, cdn) {
		get_mb_list(frm);
	},
	type: function (frm) {
		tds_calculation(frm)
	}
});

// Project Invoice BOQ
frappe.ui.form.on("Project Invoice BOQ", {
	invoice_quantity: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];

		if (child.invoice_quantity > child.act_quantity) {
			msgprint(__("Invoice Quantity cannot be greater than balance quantity.").format(child.invoice_quantity))
		}

		//if(child.invoice_quantity && child.invoice_rate){
		frappe.model.set_value(cdt, cdn, 'invoice_amount', (parseFloat(child.invoice_quantity) * parseFloat(child.invoice_rate)).toFixed(2));
		//}
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

// Project Invoice MB
frappe.ui.form.on("Project Invoice MB", {
	is_selected: function (frm, cdt, cdn) {
		calculate_totals(frm);
	},

	project_invoice_mb_remove: function (frm, cdt, cdn) {
		calculate_totals(frm);
	},

	price_adjustment_amount: function (frm, cdt, cdn) {
		calculate_totals(frm);
	},
});

// Custom Functions
var toggle_child_tables = function (frm) {
	//var boq = frappe.meta.get_docfield("Project Invoice BOQ", "item", cur_frm.doc.name);
	//boq.hidden = 1;

	if (frm.doc.invoice_type == "Direct Invoice") {
		frm.toggle_enable("project_invoice_boq", true);
		frm.toggle_enable("project_invoice_mb", false);
	} else {
		frm.toggle_enable("project_invoice_boq", false);
		frm.toggle_enable("project_invoice_mb", true);
	}
}

// Following code added by SHIV on 2019/06/18
var get_mb_list = function (frm) {
	if (frm.doc.project && frm.doc.party_type && frm.doc.party) {
		frappe.call({
			method: "erpnext.accounts.doctype.project_invoice.project_invoice.get_mb_list",
			args: {
				"project": frm.doc.project,
				"party_type": frm.doc.party_type,
				"party": frm.doc.party
			},
			callback: function (r) {
				if (r.message) {
					cur_frm.clear_table("project_invoice_mb");
					r.message.forEach(function (mb) {
						var row = frappe.model.add_child(frm.doc, "Project Invoice MB", "project_invoice_mb");
						row.entry_name = mb['name'];
						row.entry_date = mb['entry_date'];
						row.entry_amount = flt(mb['total_balance_amount']);
						row.act_entry_amount = flt(mb['total_entry_amount']);
						row.act_invoice_amount = flt(mb['total_invoice_amount']);
						row.act_received_amount = flt(mb['total_received_amount']);
						row.act_balance_amount = flt(mb['total_balance_amount']);
						row.boq = mb['boq'];
						row.boq_type = mb['boq_type'];
						row.subcontract = mb['subcontract'];
					});
					cur_frm.refresh();
				}
				else {
					cur_frm.clear_table("project_invoice_mb");
					//cur_frm.refresh();
				}
			}
		});
	} else {
		cur_frm.clear_table("project_invoice_mb");
		//cur_frm.refresh();
	}
}

var toggle_items_based_on_boq_type = function (frm) {
	var invoice_amount_editable = frm.doc.boq_type === "Milestone Based" ? true : false;

	var invoice_quantity_editable = in_list(["Item Based",
		"Piece Rate Work Based(PRW)"], frm.doc.boq_type) ? true : false;
}

var calculate_totals = function (frm) {
	var pi = frm.doc.project_invoice_boq || [];
	var mb = frm.doc.project_invoice_mb || [];
	var gross_invoice_amount = 0.0, price_adjustment_amount = 0.0, net_invoice_amount = 0.0;

	if (frm.doc.docstatus != 1) {
		if (frm.doc.invoice_type == "Direct Invoice") {
			// Direct Invoice
			for (var i = 0; i < pi.length; i++) {
				if (pi[i].invoice_amount && pi[i].is_selected == 1) {
					gross_invoice_amount += flt(pi[i].invoice_amount);
				}
			}
		}
		else {
			// MB Based Invoice
			for (var i = 0; i < mb.length; i++) {
				if (mb[i].entry_amount && mb[i].is_selected == 1) {
					gross_invoice_amount += flt(mb[i].entry_amount);
					price_adjustment_amount += flt(mb[i].price_adjustment_amount || 0.0);
				}
			}

			if (flt(frm.doc.price_adjustment_amount || 0.0) != flt(price_adjustment_amount || 0.0)) {
				cur_frm.set_value("price_adjustment_amount", flt(price_adjustment_amount));
			}

		}
		var total_deduct_amount = 0
		if (frm.doc.rebate) {
			frm.doc.rebate.map(item => {
				if (item.addition == 1) {
					total_deduct_amount -= item.amount
				}
				else {
					total_deduct_amount += item.amount
				}
			})
		}
		cur_frm.set_value("net_amount", (gross_invoice_amount - total_deduct_amount))
		net_invoice_amount = (flt(frm.doc.net_amount) + flt(frm.doc.price_adjustment_amount || 0.0) - flt(frm.doc.advance_recovery || 0.0) - flt(frm.doc.total_deduction_amount || 0.0));
		cur_frm.set_value("gross_invoice_amount", (gross_invoice_amount));
		cur_frm.set_value("net_invoice_amount", (net_invoice_amount));
		cur_frm.set_value("total_balance_amount", (flt(frm.doc.net_invoice_amount || 0) - flt(frm.doc.total_received_amount || 0) - flt(frm.doc.total_paid_amount || 0)));
	}
}

var check_uncheck_all = function (frm) {
	if (frm.doc.invoice_type == "Direct Invoice") {
		var pib = frm.doc.project_invoice_boq || [];

		for (var id in pib) {
			frappe.model.set_value("Project Invoice BOQ", pib[id].name, "is_selected", frm.doc.check_all);
		}
	}
	else {
		var mb = frm.doc.project_invoice_mb || [];

		for (var id in mb) {
			frappe.model.set_value("Project Invoice MB", mb[id].name, "is_selected", frm.doc.check_all_mb);
		}
	}
}

frappe.ui.form.on("Project Invoice Rebate Item", {
	amount: function (frm, cdt, cdn) {
		calculate_totals(frm)
		tds_calculation(frm)
	},
	addition: function (frm, cdt, cdn) {
		calculate_totals(frm)
		tds_calculation(frm)
	}
})


frappe.ui.form.on("Project Invoice Deduction", {
	amount: function (frm, cdt, cdn) {
		calculate_deductions(frm, cdt, cdn);
	},

	deductions_remove: function (frm, cdt, cdn) {
		calculate_deductions(frm, cdt, cdn);
	},

	deductions_add: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, 'cost_center', frm.doc.cost_center);
	},
});
frappe.ui.form.on("Project Invoice Advance", {
	allocated_amount: function (frm) {
		calculate_deductions(cur_frm);
	},

	advances_remove: function (frm) {
		calculate_deductions(cur_frm);
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
						var row = frappe.model.add_child(frm.doc, "Project Invoice Advance", "advances");
						row.reference_doctype = "Project Advance";
						row.reference_name = adv['name'];
						row.advance_account = adv['advance_account'];
						row.total_amount = flt(adv['balance_amount']);
                        row.advance_account = adv['advance_account']
						row.allocated_amount = 0.00;
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


function tds_calculation(frm) {
	//Set the initial value for tds rate
	var percent = 0;
	switch (cur_frm.doc.type) {
		case "Domestic Vendor":
			cur_frm.set_value("tds_rate", 2);
			percent = 2
			break;
		case "International Vendor":
			cur_frm.set_value("tds_rate", 3);
			percent = 3
			break;
		case "Rent and Consultancy":
			cur_frm.set_value("tds_rate", 5);
			percent = 5
			break;
		case "Dividend":
			cur_frm.set_value("tds_rate", 10);
			percent = 10
			break;
		default:
			cur_frm.set_value("tds_rate", 0);
			percent = 0
	}


	cur_frm.set_value("tds_taxable_amount", cur_frm.doc.net_amount);
	cur_frm.refresh_field("tds_taxable_amount")
	cur_frm.set_value("tds_amount", (cur_frm.doc.tds_rate / 100) * cur_frm.doc.tds_taxable_amount);
	cur_frm.refresh_field("tds_amount")
    frm.trigger("tds_rate")
	calculate_deductions(cur_frm)
};

function calculate_deductions(frm) {
	// Other deductions
	let total_deduction_amount = 0
	if (frm.doc.deductions) {
		frm.doc.deductions.map(item => {
			total_deduction_amount += item.amount
		})
	}

	if (frm.doc.advances) {
		frm.doc.advances.map(item => {
			total_deduction_amount += item.allocated_amount
		})
	}
	if (frm.doc.tds_amount) {
		total_deduction_amount += frm.doc.tds_amount
	}

	frm.doc.total_deduction_amount = total_deduction_amount
	cur_frm.refresh_field("total_deduction_amount")
	calculate_totals(frm)
}
