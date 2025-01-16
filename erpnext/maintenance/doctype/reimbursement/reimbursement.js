// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Reimbursement', {
	
	refresh: function(frm){
		frm.set_query("branch", function(doc){
			return {
				filters: {
					'company': doc.company,
				}
			}
		});

		frm.set_query("credit_account", function(doc){
			return {
				filters: {
					'company': doc.company,
				}
			}
		});
	},

	type: function (frm) {
		if (frm.doc.type) {
			frappe.call({
				method: "get_expense_account",
				doc: frm.doc,
				callback: function (r) {
					if (r.message) {
						cur_frm.set_value("expense_account", r.message);
						refresh_field('expense_account');
					}
				}
			})
		}
	},

	credit_account: function (frm) {
		frappe.model.get_value("Account", frm.doc.credit_account, "account_type", function (d){
			if (d.account_type == 'Payable' || d.account_type == 'Receivable'){
				cur_frm.toggle_display('party_type', 1);
			} else {
				frm.set_value("party_type", "")
				cur_frm.toggle_display('party_type', 0);
			}
			frm.set_value("party", "")
		});
	},
	party_type: function (frm) {
		frm.set_value("party", "")
	}

});

frappe.ui.form.on("Reimbursement Items", {
	amount: function(frm, cdt, cdn) {
		var total = 0;
		frm.doc.items.forEach(function(d) {total += d.amount});
		frm.set_value("amount", total)
	},
	items_remove: function (frm, cdt, cdn) {
		var total = 0;
		frm.doc.items.forEach(function(d) {total += d.amount});
		frm.set_value("amount", total)
	}
});
