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
			else{
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
		
			frm.add_custom_button(__('Eligibility Check For Maximum of 3 Domains'), function(){
				return frappe.call({
					method: "eligibility_for_domain",
					doc: cur_frm.doc,
					callback: function(r, rt) {
						frm.refresh_field("item");
						frm.reload_doc();
					},
					freeze: true,
					freeze_message: "Eligibility Check and Updating..... Please Wait"
				});
			}, __("Utilities"));

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

		cur_frm.set_query("cohort", function() {
			return {
				"filters": {
					"status": "ACTIVE"
				}
			}
		 });
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

var create_custom_buttons = function(frm){
	console.log("Hi");
	if(frm.doc.workflow_state == "Pending"){
		frm.page.set_primary_action(__('Update Deployment'), () => {
			process_payment(frm);
		});
	}
	// Option to re-process for failed and transactions from bank's end
	frm.add_custom_button(__("Reset Status to Pending"), function () {
		frappe.call({
			"method": "reset_to_pending",
			"doc": cur_frm.doc,
			callback: function(r, rt) {
					cur_frm.reload_doc();
			},
			freeze: true,
			freeze_message: "Status Resetting.... Please Wait",
		});
		}).addClass("btn-warning");
	}
