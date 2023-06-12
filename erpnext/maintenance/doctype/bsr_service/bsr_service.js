// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('BSR Service', {
	// refresh: function(frm) {

	// }
	setup: function(frm) {
		frm.set_query("item", "items", function() {
			return {
				filters: [
					["disabled", "=", 0],
					// ["is_bsr_service_item", "=", 1],
					["is_service_item", "=", 1],
				]
			}
		});
	}
});
