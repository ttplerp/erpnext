// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deployment Requisition', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.announced === 0) {
			frm.add_custom_button(__('Announcement'), function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.training_and_skilling.doctype.deployment_requisition.deployment_requisition.make_announcement",
					frm: cur_frm,
				})
			}, __('Create'));
			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},
	onload:function(frm){
		frm.set_query("event", function(){
			return {
				filters: {
					'disabled': 0,
				}
			}
		})

		frm.set_query("category", function(){
			return {
				filters: {
					'type_of_event': frm.doc.event,
					'disabled': 0,
				}
			}
		})

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
