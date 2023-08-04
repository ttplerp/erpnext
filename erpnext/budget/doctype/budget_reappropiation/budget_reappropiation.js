// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Budget Reappropiation', {
	refresh: function(frm) {
		apply_account_filter(frm)
	},
	onload:function(frm){
		apply_account_filter(frm)
	},
	budget_type:function(frm){
		apply_account_filter(frm)
	}
});
var apply_account_filter = function(frm){
	console.log()
	frm.set_query("from_account", "items", function() {
		return {
			filters: {
				company: frm.doc.company,
				is_group: 0,
				root_type:["in",["Expense","Asset"]],
				budget_type:frm.doc.budget_type
			}
		};
	});
	frm.set_query("to_account", "items", function() {
		return {
			filters: {
				company: frm.doc.company,
				is_group: 0,
				root_type:["in",["Expense","Asset"]],
				budget_type:frm.doc.budget_type
			}
		};
	});
}
