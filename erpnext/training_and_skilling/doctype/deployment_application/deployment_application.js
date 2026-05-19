// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deployment Application', {
	refresh: function(frm) {
		frm.set_value("done_manually", 1)
	}
});
