// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
// developed by Birendra on 01/03/2021

frappe.ui.form.on('Performance Evaluation', {
	setup:(frm)=>{
		apply_filter(frm)
		set_default_value(frm)

		if (frm.doc.docstatus == 1 && frappe.user.has_role(['HR Manager', 'HR User'])){
			frm.get_docfield("evaluate_target_item").allow_bulk_edit = 1;
			frm.get_docfield("evaluate_target_item").read_only = 0;
		}else{
			frm.get_docfield("evaluate_target_item").allow_bulk_edit = 0;
			frm.get_docfield("evaluate_target_item").read_only = 1;
		}
	},
	onload:(frm)=> {
		apply_filter(frm)
		set_default_value(frm)
		if(frm.doc.docstatus == 1){
			frappe.call({
				method: "check_perc_role",
				doc: frm.doc,
				callback: (r)=> {
					if (r.message == 1){
						frm.add_custom_button(__('Moderate'), () => {
							frappe.call({
								method: "moderate_performance_evaluation",
								doc: frm.doc,
								callback: (r) => {
									window.location.reload()
								}

							})
						});
					}
				}
			})
	
		}
	},
	
	refresh: (frm)=>{
		set_default_value(frm)
		add_btn(frm);

		if (frm.doc.docstatus == 0 && frappe.user.has_role(['HR Manager', 'HR User'])){
			frm.set_df_property('set_manual_approver', 'read_only', 0);
		}else{
			frm.set_df_property('set_manual_approver', 'read_only', 1);
		}
		if (frm.doc.docstatus == 1 && frappe.user.has_role(['HR Manager', 'HR User'])){
			frm.get_docfield("evaluate_target_item").allow_bulk_edit = 1;
			frm.get_docfield("evaluate_target_item").read_only = 0;
		}else{
			frm.get_docfield("evaluate_target_item").allow_bulk_edit = 0;
			frm.get_docfield("evaluate_target_item").read_only = 1;
		}
	},

	perc_required: (frm) => {
		if (frm.doc.perc_required == "Yes"){
				frappe.call({
					method: "erpnext.pms.doctype.performance_evaluation.performance_evaluation.set_perc_approver",
					"args":{
						"perc": frm.doc.perc_required
					},
					callback: (r)=> {
						console.log(r)
						frm.set_value("perc_approver", r.message)
						frm.refresh_field("perc_approver")
					}
				})
			}else{
				frm.set_value("perc_approver", '')
				frm.set_value("perc_name", '')
				frm.refresh_field("perc_approver")
				frm.refresh_field("perc_name")
			}
	},

	set_manual_approver:function(frm){
		if (flt(frm.doc.set_manual_approver) == 1){
			frm.set_df_property('approver', 'read_only', 0);
			// frm.set_df_property('approver_designation', 'read_only', 0);
		}
		else{
			frm.set_df_property('approver', 'read_only', 1);
			// frm.set_df_property('approver_designation', 'read_only', 1);
		}
	},
	pms_calendar: (frm)=>{
		get_competency(frm)
	},
	get_competency:(frm)=> {
		get_competency(frm);
	},
	// employee: (frm)=>{
	// 	get_supervisor_id(frm)
	// }
});

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
};

frappe.ui.form.on('Evaluate Target Item',{
	onload:(frm,cdt,cdn)=>{
		toggle_reqd_qty_quality(frm,cdt,cdn)
	},
	form_render:(frm,cdt,cdn)=>{
		// var row = locals[cdt][cdn]
		if ( frm.doc.docstatus == 1){
			if (frappe.user.has_role(['HR Manager', 'HR User'])){
				frappe.meta.get_docfield("Evaluate Target Item","reverse_formula",cur_frm.doc.name).read_only = 0
			}else{
				frappe.meta.get_docfield("Evaluate Target Item","reverse_formula",cur_frm.doc.name).read_only = 1
			}
		}
		frappe.meta.get_docfield("Evaluate Target Item","qty_quality",cur_frm.doc.name).read_only = frm.doc.docstatus
		frappe.meta.get_docfield("Evaluate Target Item","timeline_base_on",cur_frm.doc.name).read_only = frm.doc.docstatus
	},
	refresh:(frm,cdt,cdn)=>{
		toggle_reqd_qty_quality(frm,cdt,cdn)
	},
	timeline_achieved:(frm,cdt,cdn)=>{
		toggle_reqd_qty_quality(frm,cdt,cdn)
		calculate_timeline_rating(frm,cdt,cdn)
		calculate_score(frm,cdt,cdn)
	},
	quality_achieved:(frm,cdt,cdn)=>{
		calculate_qty_quality_rating(frm,cdt,cdn)
		calculate_score(frm,cdt,cdn)
	},
	quantity_achieved:(frm,cdt,cdn)=>{
		calculate_qty_quality_rating(frm,cdt,cdn)
		calculate_score(frm,cdt,cdn)
	},
	accept_zero_qtyquality:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		row.quality_achieved = row.quantity_achieved = 0
		frm.refresh_field('evaluate_target_item')
	},
	reverse_formula:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		if (cint(row.reverse_formula) == 0 ){
			row.accept_zero_qtyquality = 0
			frm.refresh_field('evaluate_target_item')
		}
	}
})

var set_default_value = (frm)=>{
	// frm.set_df_property('self_declaration_yes_or_no', 'reqd', frm.doc.owner == frappe.session.user)
	frm.set_df_property('employee', 'read_only', frm.doc.owner != frappe.session.user)

	// frm.set_df_property('self_declaration_yes_or_no', 'read_only', frm.doc.owner != frappe.session.user)
	frm.set_df_property('supervisor_comment', 'read_only', frm.doc.approver != frappe.session.user)

	frm.set_df_property('employee_comment', 'read_only', frm.doc.owner != frappe.session.user && !frappe.user.has_role(['HR Manager', 'HR User']))
	frm.set_df_property('supervisor_manager_comment', 'read_only', frm.doc.supervisor_manager != frappe.session.user)

	let require = cur_frm.doc.approver == frappe.session.user || cur_frm.doc.supervisor_manager == frappe.session.user
	// console.log(require)
	if (require) require = 0
	
	frm.set_df_property('agreed_by_perc', 'reqd', frm.doc.perc_required == 'Yes' && frappe.user.has_role['PERC Member'])
	frm.set_df_property('agreed_by_perc', 'read_only', !frappe.user.has_role['PERC Member'])
	if ( !frm.doc.max_rating_limit){
		frappe.call({
			method: 'set_dafault_values',
			doc: frm.doc,
			callback: (r)=> {
				frm.refresh_field("max_rating_limit")
			}
		})
	}
}

var add_btn = (frm)=>{
	if (frm.doc.docstatus == 1 && cur_frm.doc.reference){
		frm.add_custom_button(__('Create PMS Summary'), (doc)=>{
			frappe.model.open_mapped_doc({
				method: "erpnext.pms.doctype.performance_evaluation.performance_evaluation.create_pms_summary",	
				frm: cur_frm
			});
		}).addClass("btn-primary custom-create custom-create-css")
	}
}

// calculate timeline rating
var calculate_timeline_rating = (frm,cdt,cdn)=>{
	let targeted_timeline = 0
	let timeline_achieved = 0
	let timeline_rating = 0
	var row = locals[cdt][cdn]
	let limit = frm.doc.max_rating_limit ? frm.doc.max_rating_limit : 5
	targeted_timeline = row.timeline
	timeline_achieved = row.timeline_achieved

	timeline_rating = targeted_timeline / timeline_achieved * limit
	if (timeline_rating > limit ) timeline_rating = limit

	row.timeline_rating = timeline_rating
	// console.log('here',row.timeline_rating)
	frm.refresh_field('evaluate_target_item')
}
// calculate score and average
var calculate_score = (frm,cdt,cdn)=>{
	var row = locals[cdt][cdn]
	if ( (row.quality_rating || row.quantity_rating) && row.timeline_rating ){
		let qty_quality = 0
		if (row.qty_quality == 'Quality') qty_quality = row.quality_rating
		else if (row.qty_quality == 'Quantity') qty_quality = row.quantity_rating
		if (cint(row.accept_zero_qtyquality) == 1){
			row.average_rating = row.timeline_rating
		}else{
			row.average_rating = (qty_quality + row.timeline_rating)/2
		}
		row.score = row.average_rating * row.weightage / 100
		frm.refresh_field("evaluate_target_item")
	}
}
//calculate quality or quantity rating
var calculate_qty_quality_rating = (frm,cdt,cdn)=>{
	let qty_quality_achieved = 0
	let qty_quality_rating = 0
	let targeted_qty_quality = 0
	var row = locals[cdt][cdn]
	let limit = frm.doc.max_rating_limit? frm.doc.max_rating_limit:5
	if (row.qty_quality == 'Quality') {
		qty_quality_achieved = row.quality_achieved
		targeted_qty_quality = row.quality
	}
	else if (row.qty_quality == 'Quantity') {
		qty_quality_achieved = row.quantity_achieved
		targeted_qty_quality = row.quantity
	}
	if (cint(row.reverse_formula) == 1){
		if (cint(row.accept_zero_qtyquality) == 1){
			qty_quality_rating 		= 0
			row.quantity_achieved 	= 0
			row.quality_achieved	= 0
		}
		else
			qty_quality_rating = targeted_qty_quality / qty_quality_achieved * limit}
	else{
		qty_quality_rating = qty_quality_achieved / targeted_qty_quality * limit
	}
	if (qty_quality_rating > limit ) qty_quality_rating = limit
	
	if (row.qty_quality == 'Quality') row.quality_rating = qty_quality_rating
	else if (row.qty_quality == 'Quantity') row.quantity_rating = qty_quality_rating
	frm.refresh_field('evaluate_target_item')
}
var toggle_reqd_qty_quality = (frm,cdt,cdn)=>{
	var row = locals[cdt][cdn]
		if (row.qty_quality == 'Quality'){
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quality_achieved", true)
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quantity_achieved", false)
		}else if (row.qty_quality == 'Quantity'){
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quality_achieved", false)
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quantity_achieved", true)
		}else{
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quality_achieved", false)
			cur_frm.fields_dict.evaluate_target_item.grid.toggle_reqd("quantity_achieved", false)
		}
}
var get_current_user=(frm)=>{
	frappe.call({
		method: 'get_current_user',
		doc: frm.doc,
		callback:  (r) =>{
			frm.refresh_fields()
		}
	})
}

var apply_filter=(frm)=> {
	cur_frm.set_query('pms_calendar', function () {
		return {
			'filters': {
				'docstatus': 1
			}
		};
	});
}

var get_competency = (frm)=>{
	if ( frm.doc.docstatus == 1 || frm.doc.evaluate_competency_item.length > 0 || !frm.doc.__islocal ) return
	if (frm.doc.pms_group) {
		frappe.call({
			method: "get_competency",
			doc: frm.doc,
			callback: (r)=> {
				cur_frm.refresh_field("evaluate_competency_item")
			}
		})
	}
}
var get_achievement = (frm)=>{
	if (frm.doc.pms_calendar) {
		frappe.call({
			method: "get_additional_achievements",
			doc: frm.doc,
			callback: (r)=> {
				cur_frm.refresh_field("achievements_items")
			}
		})
	}else{
		frappe.throw("Select PMS Calendar to get <b>Achievements</b>")
	}
}

frappe.form.link_formatters['Employee'] = function(value, doc) {
	return value
}