// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Service', {
	refresh: function(frm) {
		frm.set_query("item_sub_group", function(){
			return {
				"filters": {
					"category":frm.doc.item_group
				}
			}
		});
	}
});
