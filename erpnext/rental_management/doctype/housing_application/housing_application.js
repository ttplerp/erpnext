// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Housing Application', {
	refresh: function(frm) {
		// Write your magic codes here
		if(frm.doc.docstatus==1 && frm.doc.application_status!="Alloted" && !frm.doc.tenant_id){
			frm.page.set_primary_action(__('Create Allotment'), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.rental_management.doctype.housing_application.housing_application.make_tenant_information",
					frm: cur_frm
				});
			});
		}
	},
});
