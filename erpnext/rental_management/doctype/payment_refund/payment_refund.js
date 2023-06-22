// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Payment Refund', {
	refresh: function(frm) {
		if (frm.is_new()) {
			frappe.model.get_value('Company', frm.doc.company, ['default_bank_account'], function(d){
				cur_frm.set_value("account_refund_from", d.default_bank_account);
			});
		}
	},
	type: function (frm) {
		if (frm.doc.type == 'Excess Amount') {
			frappe.model.get_value('Rental Account Setting',{'name': 'Rental Account Setting'}, ['excess_payment_account'], function(d){
				cur_frm.set_value("account_refund_to", d.excess_payment_account);
			});
		}
		if (frm.doc.type == 'Security Deposit') {
			frappe.model.get_value('Rental Account Setting',{'name': 'Rental Account Setting'}, ['security_deposit_account'], function(d){
				cur_frm.set_value("account_refund_to", d.security_deposit_account);
			});
		}
	}
});
