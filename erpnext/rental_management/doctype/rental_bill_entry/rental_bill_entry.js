// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rental Bill Entry', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 0 && frm.doc.bill_created == 0){
			cur_frm.add_custom_button(__('Get Tenants'), function(doc) {
				frm.events.get_tenant_list(frm)
			},__("Create"))
		}
		if(frm.doc.docstatus == 1 && frm.doc.bill_created == 0){
			cur_frm.add_custom_button(__('Create Rental Bill'), function(doc) {
				frm.events.create_rental_bill(frm)
			},__("Create"))
		}
		if(frm.doc.docstatus == 1 && frm.doc.bill_created == 1 && frm.doc.bill_submitted == 0){
			cur_frm.add_custom_button(__('Submit Rental Bill'), function(doc) {
				frm.events.submit_rental_bill(frm)
			},__("Create"))
		}
		if(frm.doc.number_of_rental_bills != 0 && (frm.doc.number_of_rental_bills == frm.doc.successful) && frm.doc.bill_submitted == 0){
			cur_frm.add_custom_button(__('Remove Rental Bill'), function(doc) {
				frm.events.remove_rental_bill(frm)
			},__("Create"))
		}
	},
	get_tenant_list:function(frm){
		// frm.set_value("number_of_rental_bills", 0);
		// frm.refresh_field("number_of_rental_bills");
		frappe.call({
			method:"get_tenant_list",
			doc:frm.doc,
			callback:function(r){
				// console.log(r.message);
				// frm.set_value("number_of_rental_bills", r.message);
				// frm.refresh_field("number_of_rental_bills");
				frm.refresh_field("items");
				frm.dirty();
				// cur_frm.reload_doc();
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Getting Tenants.....</span>'
		})
	}, 
	create_rental_bill:function(frm){
		frappe.call({
			method:"create_rental_bill",
			doc:frm.doc,
			callback:function(r){
				// console.log(r.message);
				// frm.set_value("successful", r.message["successful"]);
				// frm.set_value("failed", r.message["failed"]);
				// frm.refresh_field("successful");
				// frm.refresh_field("failed");
				// frm.refresh_field("items");
				// frm.dirty();
				cur_frm.reload_doc();
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Getting Tenants.....</span>'
		})
	}, 
	submit_rental_bill:function(frm){
		frappe.call({
			method:"submit_rental_bill",
			doc:frm.doc,
			callback:function(r){
				cur_frm.reload_doc();
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Getting Tenants.....</span>'
		})
	}, 
	remove_rental_bill:function(frm){
		frappe.call({
			method:"remove_rental_bill",
			doc:frm.doc,
			callback:function(r){
				cur_frm.reload_doc();
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Getting Tenants.....</span>'
		})
	}, 

});
