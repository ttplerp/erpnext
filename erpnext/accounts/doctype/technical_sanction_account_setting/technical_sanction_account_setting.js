// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Technical Sanction Account Setting', {
	// refresh: function(frm) {

	// }
	setup: function(frm) {
		frm.set_query("expense_account", function(){
			return {
				"filters": [
					["is_group", "=", 0],
					["freeze_account", "=", "No"],
					// ["status", "=", "Allocated"],
				]
			};
		});
	}
});
