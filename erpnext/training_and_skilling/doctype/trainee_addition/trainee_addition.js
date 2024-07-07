// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Trainee Addition', {
	refresh: function(frm) {
		frm.set_query("training_management", function() {
			return {
				filters: {
					"status": ["in", "Approved, On Going"],
				}
			}
		});
	}
});
