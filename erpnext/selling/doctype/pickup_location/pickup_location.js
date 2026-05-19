// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pickup Location', {
	// refresh: function(frm) {

	// }
	onload:function(frm){
		frm.set_query("branch", function(){
			return {
				filters: {
					'disabled': 0,
					'company': frm.doc.company
				}
			}
		})
		frm.set_query("warehouse", function(){
			return {
				filters: {
					'disabled': 0,
					'is_group': 0,
					'company': frm.doc.company
				}
			}
		})
	}
});
