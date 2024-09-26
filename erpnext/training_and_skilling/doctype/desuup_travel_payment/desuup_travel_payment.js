// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Travel Payment', {
	refresh: function(frm) {
		frm.set_query("branch", function(){
			return {
				filters: {
					'company': frm.doc.company,
				}
			}
		});

		frm.set_query("training_management", function(){
			return {
				filters: {
					'status': 'On Going',
				}
			}
		});
	},

	get_desuups: function (frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'get_desuup_details',
			callback: function(r) {
				// if (r.message){
					frm.refresh_field("items");
					frm.dirty();
				// }
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching Desuup Records...</span>'
		});
	},
});
