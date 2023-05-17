// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Building Category', {
	// refresh: function(frm) {

	// }
	building_category: function(frm) {
		if(frm.doc.__islocal) {
			// add missing " " arg in split method
			let parts = frm.doc.building_category.split(" ");
			let abbr = $.map(parts, function (p) {
				return p? p.substr(0, 1) : null;
			}).join("");
			frm.set_value("abbr", abbr);
		}
	},
});
