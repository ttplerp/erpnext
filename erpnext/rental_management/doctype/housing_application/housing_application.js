// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Housing Application', {

	// validate: function(frm) {
    //     // if (frm.doc.docstatus == 0 && frm.doc.application_status =="Pending") {
    //     //     frappe.throw('Cannot submit the document while it is pending or cannot change the status to pending once set.');
            
    //     // }
	// },

	building_classification: function(frm){
		
		
	
	},
	
	

	refresh: function(frm) {
		var value = frm.doc.building_classification;

		// console.log(value)


		frm.set_query("flat_no", function(frm) {
			
			return {
				filters: [
					["building_classification", "=", value],
					["status","!=","Allocated"]
					
				]
			}
		});
		
		// Write your magic codes here
		if(frm.doc.docstatus==1 && frm.doc.application_status=="Allotted" && !frm.doc.tenant_id){
			frm.page.set_primary_action(__('Create Allotment'), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.rental_management.doctype.housing_application.housing_application.make_tenant_information",
					frm: cur_frm
				});
			});
		}
	},
});
