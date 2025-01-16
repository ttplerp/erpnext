// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Approver Settings', {
	refresh: function(frm) {
		frm.set_query("document_type", function(doc){
			return {
				filters: {
					'is_submittable': 1
				}
			}
		})
	}
});
