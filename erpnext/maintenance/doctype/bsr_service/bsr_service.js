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
					["is_bsr_service_item", "=", 1],
					// ["is_service_item", "=", 1],
				]
			}
		});
	},
	get_bsr_item: function(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'get_bsr_item',
			callback: function(r) {
				if (r.message){
					frm.refresh_field("items");
					frm.dirty();
				}
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching BSR Service Items...</span>'
		});
	}
});
