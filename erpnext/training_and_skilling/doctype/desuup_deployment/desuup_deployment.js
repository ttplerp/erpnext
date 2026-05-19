// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Deployment', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.completed === 0 && frm.doc.end_date < get_today()) {
			frm.add_custom_button(__('Complete Deployment'), function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.training_and_skilling.doctype.desuup_deployment.desuup_deployment.complete_deployment",
					frm: cur_frm,
				})
			}, __('Create'));
			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},
	get_applicants: function(frm) {
		if(frm.doc.deployment_announcement){
			return frappe.call({
				method: "get_applicants",
				doc: frm.doc,
				callback: function(r, rt) {
					frm.refresh_field("items");
					frm.refresh_fields();
				},
				freeze: true,
				freeze_message: "Loading applicants..... Please Wait"
			});
		}else{
			frappe.throw("Deployment Announcement reference is missing. ")
		}
	},
});
