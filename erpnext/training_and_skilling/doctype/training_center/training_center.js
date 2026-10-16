// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Center', {
	onload: function(frm) {
		frm.set_query("dzongkhag", function(){
			return {
				filters: {
					'country_name': frm.doc.country,
					'disabled': 0,
				}
			}
		})

		frm.set_query("gewog", function(){
			return {
				filters: {
					'dzongkhag': frm.doc.dzongkhag,
					'disabled': 0,
				}
			}
		})
	}
});
