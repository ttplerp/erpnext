// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CBS Connectivity', {
	// refresh: function(frm) {

	// }
	test_connectivity: function(frm){	
		return frappe.call({
			method: "erpnext.cbs_integration.doctype.cbs.test_connectivity",
			callback: function(a, b) {
			},
			freeze: true,
			freeze_message: 'Connecting...'
		});
	}
});

