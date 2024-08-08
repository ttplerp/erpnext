// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Work Competency', {
	refresh: function(frm) {
		frm.toggle_display("naming_series", 1);
		if (!frm.doc.__islocal) {
			frappe.meta.get_docfield('Work Competency', "naming_series", frm.doc.name).read_only=1;
			frm.refresh_field("naming_series")
		}
	}

});
