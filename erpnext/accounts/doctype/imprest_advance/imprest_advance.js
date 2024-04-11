// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Imprest Advance', {
	refresh: function(frm) {
		// frm.set_query('party', function() {
		// 	return {
		// 		filters: {
		// 			"branch": frm.doc.branch,
		// 			"status":"Active"
		// 		}
		// 	}
		// });
		frm.set_query("project", function() {
			return {
				"filters": {
					"branch": frm.doc.branch
				}
			}
		 });
	},
	amount: function(frm){
		if (frm.doc.amount > 0 ){
			frm.set_value("balance_amount",frm.doc.amount)
			frm.set_value("adjusted_amount",0)
		}
	},

	// party: function(frm){
	// 	frm.set_query("party", function() {
	// 		return {
	// 			"filters": {
	// 				"branch": frm.doc.branch
	// 			}
	// 		}
	// 	 });
	// },
	project: function(frm){
		frm.set_query("project", function() {
			return {
				"filters": {
					"branch": frm.doc.branch
				}
			}
		 });
	},
});
