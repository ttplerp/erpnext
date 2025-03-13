// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("bank_account", "bank_name", "bank_name");	
cur_frm.add_fetch("bank_account", "bank_branch", "bank_branch");	
cur_frm.add_fetch("bank_account", "bank_account_type", "bank_account_type");
cur_frm.add_fetch("bank_account", "bank_account_no", "bank_ac_no");

frappe.ui.form.on('Tax Payment', {
	setup: function(frm) {
		frm.set_query("tds_remittance", function(){
			return {
				filters: {
					'branch': frm.doc.branch,
					'docstatus': 1
				}
			}
		});
	},

	onload: function(frm) {
		create_custom_buttons(frm);

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
		create_custom_buttons(frm);
	},

	bank_ac_no: function(frm){
		fetch_bank_balance(frm);
	},

	get_outstanding: function(frm) {
		if(frm.doc.dv_number) {			
			frappe.call({
				method: "get_outstanding_amount",
				doc: frm.doc,
				callback: function(r) {
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

var create_custom_buttons = function(frm){
	if(!frm.is_new() && !frm.is_dirty()){
		if(frm.doc.docstatus == 1){
			if(frm.doc.status == "Pending"){
				frm.page.set_primary_action(__('Process Payment'), () => {
					process_payment(frm);
				});
			}
		}
	}
}

var process_payment = function(frm){
	frappe.call({
		method: "process_payment",
		doc: frm.doc,
		callback: function(r){
			cur_frm.reload_doc();
		},
		freeze: true,
        freeze_message: "Processing payment.... Please Wait",
	})
}