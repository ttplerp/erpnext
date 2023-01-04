// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Reimbursement', {
	purpose: function(frm){
		if(frm.doc.purpose == 'Hiring/Transportation'){
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Maintenance Accounts Settings",
					fieldname: "hire_expense_account",
				},
				callback: function (r) {
					if (r.message) {
						cur_frm.set_value("expense_account", r.message.hire_expense_account);
						refresh_field('expense_account');
					}
				}
			});
		}
		else if(frm.doc.purpose == 'POL/Maintenance'){
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Maintenance Accounts Settings',
					fieldname: "default_pol_advance_account"
				},
				callback: function (r) {
					if (r.message) {
						cur_frm.set_value("expense_account", r.message.pol_advance_account);
						refresh_field('expense_account');
					}
				}
			});
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
