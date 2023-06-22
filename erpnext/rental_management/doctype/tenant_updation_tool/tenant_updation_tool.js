// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tenant Updation Tool', {
	// refresh: function(frm) {

	// },
	setup: function(frm) {
		frm.set_query("new_tenant_department", function(){
			return {
				"filters": [
					["ministry_agency", "=", frm.doc.new_ministry_agency]
				]
			};
		});
	}
});
