// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Locations', {
	// refresh: function(frm) {

	// }
	setup: function (frm) {
		frm.set_query("dzongkhag", function () {
			return {
				"filters": {
					"is_dzongkhag": 1
				}
			};
		});
	},
});
