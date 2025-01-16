// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Branch', {
	refresh: function(frm) {
		frm.set_query("expense_bank_account", function(doc){
			return {
				filters: {
					'company': doc.company,
					'account_type': 'Bank'
				}
			}
		});

	}
});
