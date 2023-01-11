// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Update Deployment Category', {
	// refresh: function(frm) {

	// }

	get_deployment_title: function(frm){
		return frappe.call({
			method: "get_deployment_title",
			doc: cur_frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("item");
			},
			freeze: true,
			freeze_message: "Fetching Data and Updating..... Please Wait"
		});
	}
});
