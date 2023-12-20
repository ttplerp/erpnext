// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Equipment Category', {
	// refresh: function(frm) {

	// }
	enable_pol_receive_account: function(frm) {
		console.log('Here');
		frappe.call({
			method: "get_pol_receive_account",
			doc: frm.doc,
			callback: function(r) {
				frm.set_value("pol_receive_account", r.message);
				frm.refresh_field("pol_receive_account");
			}
		})
	}
});
