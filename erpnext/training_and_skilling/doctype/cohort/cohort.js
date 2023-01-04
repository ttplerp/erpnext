// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cohort', {
	// refresh: function(frm) {

	// }
	fetch_application: function(frm) {
		return frappe.call({
			method: "get_applicants",
			doc: cur_frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("applicant");
				frm.refresh_fields();
			},
			freeze: true,
			freeze_message: "Fetching Data and Updating..... Please Wait"
		});
	},
});
