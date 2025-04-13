// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Daily Cash Register', {
	refresh: function(frm) {
		frm.set_query("branch", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"is_department": "1",
				}
			};
		});
		frm.set_query("cash_account", function() {
			return {
				"filters": {
					"account_type": "Cash",
					"company": frm.doc.company,
				}
			};
		});
	},
	net_amount: function(frm) {
		frm.set_value('over_short', frm.doc.closing_balance - frm.doc.net_amount);
	},
	fetch_cash_in_entries: function(frm) {
		frappe.call({
			method: "get_gl_entries",
			doc: frm.doc,
			cash_in_out: "In",
			callback: function(r){
				console.log(r.message);
				frm.refresh_field("cash_in_entries");
			}
		})
	},
	fetch_cash_out_entries: function(frm) {
		frappe.call({
			method: "get_gl_entries",
			doc: frm.doc,
			cash_in_out: "Out",
			callback: function(r){
				console.log(r.message);
				frm.refresh_field("cash_out_entries");
			}
		})
	},
});
