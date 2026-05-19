// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Online Shopping Settings', {
	refresh: function(frm) {
		frm.set_query("item_code", "items", function (doc, cdt, cdn) {
		  return {
		    "filters": {
		      "is_selling_item": 1 
		    },
		  };
		});
	}
});
