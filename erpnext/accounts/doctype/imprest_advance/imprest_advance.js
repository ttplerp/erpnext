// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Imprest Advance', {
	// refresh: function(frm) {

	// }
	amount: function(frm){
		if (frm.doc.amount > 0 ){
			cur_frm.set_value("balance_amount",frm.doc.amount)
			cur_frm.set_value("adjusted_amount",0)
		}
	},

	party: function(frm){
		frm.set_query('party', function(doc, cdt, cdn) {
			return {
				filters: {
					"branch": frm.doc.branch
				}
			};
		});
	}
});
