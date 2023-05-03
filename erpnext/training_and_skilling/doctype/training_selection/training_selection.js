// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Selection', {
	onload: function(frm) {
	},
	refresh: function(frm) {
		if(frm.doc.workflow_state == "Selection Completed") {
			var flag = 0
			$.each(frm.doc.item || [], function(i, row) {
				if(!row.offer_letter_sent && row.confirmation_status == "Selected"){
					flag = 1;
					console.log("Dessup ID : " + row.did);
					return;
				}
			});
			if(flag || !frm.doc.offer_letter_sent){
				frm.page.set_primary_action(__('Send Offer Letter'), () => {
					return frappe.call({
						method: "send_offer_letter",
						doc: cur_frm.doc,
						callback: function(r, rt) {
							frm.refresh_field("item");
							frm.refresh();
							frm.reload_doc();
						},
						freeze: true,
						freeze_message: "Sending DSP Offer Letter..... Please Wait"
					});
				});
			}
			else if(!frm.doc.training_management){
				frm.page.set_primary_action(__('Create Training'), () => {
					return frappe.call({
						method: "create_training",
						doc: cur_frm.doc,
						callback: function(r, rt) {
							frm.refresh_field("item");
							frm.refresh();
							frm.reload_doc();
						},
						freeze: true,
						freeze_message: "Creating Training Records..... Please Wait"
					});
				});
			}
		}
		if(frm.doc.workflow_state == "Pending") {
			frm.add_custom_button(__('Update Deployment'), function(){
				return frappe.call({
					method: "update_desuup_deployment",
					doc: cur_frm.doc,
					callback: function(r, rt) {
						frm.refresh_field("item");
						frm.reload_doc();
					},
					freeze: true,
					freeze_message: "Fetching Deplpoyment and Updating..... Please Wait"
				});
			}, __("Utilities"));
		}

		if(frm.doc.workflow_state == "Selection In Progress") {
			frm.add_custom_button(__('Check With Barred List'), function(){
				return frappe.call({
					method: "check_barred",
					doc: cur_frm.doc,
					callback: function(r, rt) {
						frm.refresh_field("item");
						frm.reload_doc();
					},
					freeze: true,
					freeze_message: "Checking dessuup in Barred list..... Please Wait"
				});
			}, __("Utilities"));
		
			if(!frm.doc.disable_eligibility_for_programme) {
				frm.add_custom_button(__('Eligibility Check For Maximum of 3 Programmes'), function(){
					return frappe.call({
						method: "eligibility_for_programme",
						doc: cur_frm.doc,
						callback: function(r, rt) {
							frm.refresh_field("item");
							frm.reload_doc();
						},
						freeze: true,
						freeze_message: "Eligibility Check and Updating..... Please Wait"
					});
				}, __("Utilities"));
			}

			frm.add_custom_button(__('Calculate Deployment Points'), function(){
				return frappe.call({
					method: "calculate_points",
					doc: cur_frm.doc,
					callback: function(r, rt) {
						frm.refresh_field("item");
						frm.reload_doc();
					},
					freeze: true,
					freeze_message: "Calculating Deplpoyment Points and Updating..... Please Wait"
				});
			}, __("Utilities"));
		}

		if(frm.doc.workflow_state == "Points Calculation Completed") {
			frm.add_custom_button(__('Check Course Pre-Requisite'), function(){
				return frappe.call({
					method: "check_pre_requisites",
					doc: cur_frm.doc,
					callback: function(r, rt) {
						frm.refresh_field("item");
						frm.reload_doc();
					},
					freeze: true,
					freeze_message: "Point Calculation and Updating..... Please Wait"
				});
			}, __("Utilities"));
		}

		if(frm.doc.workflow_state == "Points Calculation Completed") {
			frm.add_custom_button(__('Applicant Shortlisting and Ranking'), function(){
				return frappe.call({
					method: "applicant_shortlisting",
					doc: cur_frm.doc,
					callback: function(r, rt) {
						frm.refresh_field("item");
						frm.reload_doc();
					},
					freeze: true,
					freeze_message: "Shortlisting and Ranking..... Please Wait"
				});
			}, __("Utilities"));
		}
		/*
		cur_frm.set_query("cohort", function() {
			return {
				"filters": {
					"status": "ACTIVE"
				}
			}
		 }); */
	},
	cohort: function(frm){
		cur_frm.set_query("course", function() {
			return {
				 query: "erpnext.training_and_skilling.doctype.training_selection.training_selection.get_courses",
				 filters: {
					'cohort': frm.doc.cohort
				    }
			      }
        	});
	},
	get_applicants: function(frm) {
		return frappe.call({
			method: "get_applicants",
			doc: cur_frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("item");
				frm.refresh_fields();
			},
			freeze: true,
			freeze_message: "Fetching Data and Updating..... Please Wait"
		});
	},
	
});