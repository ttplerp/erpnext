// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("bank_account", "bank_account_no", "bank_ac_no");

frappe.ui.form.on('Tax Payment', {
	onload: function(frm) {
		frm.set_query("bank_account", function() {
			return {
				query: "erpnext.accounts.doctype.bank_payment.bank_payment.get_paid_from",
				filters: {
					branch: frm.doc.branch
				}
			};
		});
	},

	refresh: function(frm) {

	},

	bank_account_no: function(frm){
		fetch_bank_balance(frm);
	},

	get_outstanding: function(frm) {
		if(frm.doc.dv_number) {			
			frappe.call({
				method: "get_outstanding_amount",
				doc: frm.doc,
				callback: function(r) {
					// frm.set_value("outstanding_amount", r.message.outstanding_amount);
					frm.refresh_fields();
				}
			})
		}
	}
});

var fetch_bank_balance = function(frm){
	if(frm.doc.bank_ac_no){
		frappe.call({
			method: "erpnext.integrations.bank_api.fetch_balance",
			args: {
				account_no: frm.doc.bank_ac_no,
			},
			callback: function(r) {
				if(r.message) {
					console.log(r.message);
					if(r.message.status == "0")
						frm.set_value("bank_balance", r.message.balance_amount);
					else	
						frappe.throw("Unable to fetch Bank Balance");
				}
			}
		});
	}
}