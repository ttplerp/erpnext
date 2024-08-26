// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Apprentice Addition', {
	onload: (frm) => {
		frm.set_query('desuup_deployment_entry', function(doc) {
			return {
				filters: {
					"status": ["in", "Approved, On Going"],
				}
			};
		});
	},
	// refresh: function(frm) {

	// }
});
