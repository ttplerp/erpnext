// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deployment Announcement', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.deployment_created === 0 && ["Deployment", "Desuung National Service"].includes(frm.doc.type_of_deployment)) {
			frm.add_custom_button(__('Deployment'), function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.training_and_skilling.doctype.deployment_announcement.deployment_announcement.make_deployment",
					frm: cur_frm,
				})
			}, __('Create'));
		}
		if (frm.doc.docstatus === 1 && frm.doc.deployment_created === 0 && ["Skilling"].includes(frm.doc.type_of_deployment)) {
			frm.add_custom_button(__('Select Trainees'), function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.training_and_skilling.doctype.deployment_announcement.deployment_announcement.make_training_selection",
					frm: cur_frm,
				})
			}, __('Create'));
		}
		frm.page.set_inner_btn_group_as_primary(__('Create'));
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

		frm.set_query("cohort", function(){
			return {
				filters: {
					'status': "ACTIVE",
				}
			}
		})
	},
	cohort: function(frm){
		cur_frm.set_query("course", function() {
			return {
				 query: "erpnext.training_and_skilling.doctype.deployment_announcement.deployment_announcement.get_courses",
				 filters: {
					'cohort': frm.doc.cohort
				    }
			      }
        	});
	},
});
