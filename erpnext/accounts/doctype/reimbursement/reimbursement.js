// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Reimbursement', {
	onload: function(frm){
		frm.set_query('expense_account', 'items', function() {
			return {
				"filters": {
					"account_type": "Expense Account"
				}
			};
		});
	},

	"get_imprest_advance":function(frm){
		get_imprest_advance(frm)
	},

	branch: function(frm){
		frm.set_value('party_type', '');
		frm.set_value('party', '');
		frm.set_value('purpose', '');
		frm.set_value('items', '');
		frm.refresh_field('items')
		frm.set_value('imprest_advance_list', '');
		frm.refresh_field('imprest_advance_list')

		frm.set_query('party', function(doc, cdt, cdn) {
			return {
				filters: {
					"branch": frm.doc.branch
				}
			};
		});
	}
});

frappe.ui.form.on("Reimbursement Items", {
	amount: function(frm, cdt, cdn){
		get_imprest_advance(frm)
	}
})

var get_imprest_advance = function(frm){
	frm.set_value('total_amount', 0);
	frappe.call({
		method: 'populate_imprest_advance',
		doc: frm.doc,
		callback:  () =>{
			frm.refresh_field('imprest_advance_list')
			cur_frm.refresh_fields()
		}
	})
}
