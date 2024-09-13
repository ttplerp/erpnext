// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
//  developed by Birendra on 15/02/2021
frappe.ui.form.on('Review', {
	refresh: function(frm){
		if (frm.doc.docstatus == 1) {
			const reviewFlow = {
				'Review I': 'Review II',
				'Review II': 'Review III',
				'Review III': 'Review IV',
				'Review IV': 'Create Evaluation'
			};
			var btn_title = `Create ${reviewFlow[frm.doc.review_type]}`
			if (frm.doc.review_type === 'Review IV') {
				cur_frm.add_custom_button(__(btn_title), ()=>{
					frappe.model.open_mapped_doc({
						method: "erpnext.pms.doctype.review.review.create_evaluation",	
						frm: cur_frm
					});
				}).addClass("btn-primary custom-create custom-create-css")
			} else if (reviewFlow[frm.doc.review_type]) {
				// console.log(`Create ${reviewFlow[frm.doc.review_type]}`);
				// create_review(reviewFlow[frm.doc.review_type]);
				
				let review_level = reviewFlow[frm.doc.review_type]

				cur_frm.add_custom_button(__(btn_title), ()=>{
					frappe.model.open_mapped_doc({
						method: "erpnext.pms.doctype.review.review.create_review",	
						frm: cur_frm,
						args: {review_level: review_level, target_id: cur_frm.doc.target}
					});
				}).addClass("btn-primary custom-create custom-create-css")
			} else {
				console.log("Value missing for Review Type");
			}
		
		}

		// if (frm.doc.docstatus == 1 && frm.doc.review_type == 'Review IV'){
		// 	cur_frm.add_custom_button(__('Create Evaluation'), ()=>{
		// 		frappe.model.open_mapped_doc({
		// 			method: "erpnext.pms.doctype.review.review.create_evaluation",	
		// 			frm: cur_frm
		// 		});
		// 	}).addClass("btn-primary custom-create custom-create-css")
		// }
		// else if (frm.doc.docstatus == 1 && frm.doc.review_type == 'Review I'){
		// 	cur_frm.add_custom_button(__('Create Review II'), ()=>{
		// 		frappe.model.open_mapped_doc({
		// 			method: "erpnext.pms.doctype.review.review.create_review",	
		// 			frm: cur_frm,
		// 			args: {review_level: "Review II", target_id: cur_frm.doc.target}
		// 		});
		// 	}).addClass("btn-primary custom-create custom-create-css")
		// }
		// else if (frm.doc.docstatus == 1 && frm.doc.review_type == 'Review II'){
		// 	cur_frm.add_custom_button(__('Create Review III'), ()=>{
		// 		frappe.model.open_mapped_doc({
		// 			method: "erpnext.pms.doctype.review.review.create_review",	
		// 			frm: cur_frm,
		// 			args: {review_level: "Review III", target_id: cur_frm.doc.target}
		// 		});
		// 	}).addClass("btn-primary custom-create custom-create-css")
		// }
		// else if (frm.doc.docstatus == 1 && frm.doc.review_type == 'Review III'){
		// 	cur_frm.add_custom_button(__('Create Review IV'), ()=>{
		// 		frappe.model.open_mapped_doc({
		// 			method: "erpnext.pms.doctype.review.review.create_review",	
		// 			frm: cur_frm,
		// 			args: {review_level: "Review IV", target_id: cur_frm.doc.target}
		// 		});
		// 	}).addClass("btn-primary custom-create custom-create-css")
		// }


		// if (frm.doc.rev_workflow_state == "Waiting Approval" && frappe.user.has_role(['HR Manager', 'HR User'])){
		// 	cur_frm.add_custom_button(__('Manual Approval'), ()=>{
		// 		frappe.call({
		// 			method: "erpnext.pms.doctype.review.review.manual_approval_for_hr",
		// 			frm: cur_frm,
					
		// 			args: {
		// 				name: frm.doc.name,
		// 				employee: frm.doc.employee,
		// 				pms_calendar: frm.doc.pms_calendar,
		// 			},
		// 			callback:function(){
		// 				cur_frm.reload_doc()
		// 			}				
		// 		});
		// 	}).addClass("btn-primary custom-create custom-create-css");
		// }
		if (frm.doc.approver == frappe.session.user){
			frappe.meta.get_docfield("Review Target Item","appraisees_remarks",cur_frm.doc.name).read_only = frappe.session.user == frm.doc.approver
			frappe.meta.get_docfield("Review Competency Item","appraisees_remarks",cur_frm.doc.name).read_only = frappe.session.user == frm.doc.approver
			frappe.meta.get_docfield("Additional Achievements","appraisees_remarks",cur_frm.doc.name).read_only = frappe.session.user == frm.doc.approver
		}
		// if (frm.doc.docstatus != 1 && frappe.user.has_role(['HR Manager', 'HR User'])){
		// 	frm.add_custom_button(__('Manual Approval'), ()=>{
		// 		frappe.call({
		// 			method: "erpnext.pms.doctype.review.review.manual_approval_for_hr",
		// 			frm: cur_frm,
		// 			args: {
		// 				name: frm.doc.name,
		// 				employee: frm.doc.employee,
		// 				pms_calendar: frm.doc.pms_calendar,
		// 			},
		// 			callback:function(){
		// 				cur_frm.reload_doc()
		// 			}				
		// 		});
		// 	}).addClass("btn-primary custom-create custom-create-css");
		// }
	},
	// set_manual_approver:function(frm){
	// 	if (flt(frm.doc.set_manual_approver) == 1){
	// 		frm.set_df_property('approver', 'read_only', 0);
	// 	}
	// 	else{
	// 		frm.set_df_property('approver', 'read_only', 1);
	// 	}
	// },
	onload: function(frm){
		apply_filter(frm)
	},
	get_target: function(frm){
		get_target(frm);
	},
	pms_calendar: function(frm){
		cur_frm.refresh_fields()
	}
})
cur_frm.cscript.approver = function(doc){
	console.log(doc.approver)
	frappe.call({
		"method": "set_approver_designation",
		"doc": doc,
		"args":{
			"approver": doc.approver
		},
		callback: function(r){
			if(r){
				console.log(r.message)
				cur_frm.set_value("approver_designation",r.message);
				cur_frm.refresh_field("approver_designation")

			}
		}
	})
}

var add_btn = function(frm){
	if (frm.doc.docstatus == 1){
		frm.add_custom_button(__('Create Evaluation'), ()=>{
			frappe.model.open_mapped_doc({
				method: "erpnext.pms.doctype.review.review.create_evaluation",	
				frm: cur_frm
			});
		}).addClass("btn-primary custom-create custom-create-css")
	}
}

var hr_add_btn =function(frm){
	if (frm.doc.rev_workflow_state == "Waiting Approval" && frappe.user.has_role(['HR Manager', 'HR User'])){
		frm.add_custom_button(__('Manual Approval'), ()=>{
			frappe.call({
				method: "erpnext.pms.doctype.review.review.manual_approval_for_hr",
				frm: cur_frm,
				
				args: {
					name: frm.doc.name,
					employee: frm.doc.employee,
					pms_calendar: frm.doc.pms_calendar,
				},
				callback:function(){
					cur_frm.reload_doc()
				}				
			});
		}).addClass("btn-primary custom-create custom-create-css");
	}
}

var apply_filter=function(frm){
	cur_frm.set_query('pms_calendar',  () =>{
		return {
			'filters': {
				'name': frappe.defaults.get_user_default('fiscal_year'),
				'docstatus': 1
			}
		};
	});
}

var get_target = function(frm){
	//get traget from py file
	if (frm.doc.required_to_set_target && frm.doc.pms_calendar) {
		frappe.call({
			method: 'get_target',
			doc: frm.doc,
			callback:  (r) =>{
				frm.refresh_field("review_target_item")
			}
		})
	}else{
		frappe.throw("Select PMS Calendar to get <b>Target</b>")
	}
}

frappe.ui.form.on('Review Target Item',{
	form_render:function(frm,cdt,cdn){
		var row = locals[cdt][cdn]
		frappe.meta.get_docfield("Review Target Item","qty_quality",cur_frm.doc.name).read_only = frm.doc.docstatus
		frappe.meta.get_docfield("Review Target Item","timeline_base_on",cur_frm.doc.name).read_only = frm.doc.docstatus
		// frm.refresh_field('items')
	},
})

frappe.form.link_formatters['Employee'] = function(value, doc) {
	return value
}