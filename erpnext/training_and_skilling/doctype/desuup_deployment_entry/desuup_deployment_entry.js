// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Deployment Entry', {
	onload: function (frm) {
		if(frm.doc.status=="On Going" || frm.doc.status=="Approved"){
			frm.get_field('items').grid.cannot_add_rows = true;
	   	};

	   	frm.set_query('branch', function(doc) {
			return {
				filters: {
					"company": frm.doc.company,
				}
			}
		}); 
	},
	
	// refresh: function(frm) {

	// }
});
