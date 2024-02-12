// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Advance', {
	refresh: function (frm) {

	},

	setup: function (frm) { 
		frm.set_query("advance_type", function () { 
			return {
				filters : { 
					"party_type": frm.doc.party_type
				}
			}
		})
	},

	// party_type: function (frm) {
	// 	payment_type = "Pay"
	// 	if (frm.doc.party_type == "Supplier") {
	// 		payment_type = "Receive"
	// 	} 
	// 	frm.set_value("payment_type", payment_type);
	// }
});
