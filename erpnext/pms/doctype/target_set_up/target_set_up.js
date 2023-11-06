// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
// developed by Birendra on 01/02/2021
frappe.ui.form.on('Target Set Up', {
	setup:(frm)=>{
	},
	pms_calendar: (frm)=>{
		load_required_values(frm)
		cur_frm.fields_dict['common_target'].grid.get_field('reference').get_query = function(doc, cdt, cdn) {
			return {
				query: "erpnext.pms.doctype.target_set_up.target_set_up.apply_target_filter",
				filters: {
					'parent': doc.pms_calendar
				}
			}
		}
	},
	refresh: (frm)=>{
		add_btn(frm)
		hr_add_btn(frm)

		if (frm.doc.docstatus == 0 && frappe.user.has_role(['HR Manager', 'HR User'])){
			frm.set_df_property('set_manual_approver', 'read_only', 0);
		}else{
			frm.set_df_property('set_manual_approver', 'read_only', 1);
		}
	},
	set_manual_approver:function(frm){
		if (flt(frm.doc.set_manual_approver) == 1){
			frm.set_df_property('approver', 'read_only', 0);
		}
		else{
			frm.set_df_property('approver', 'read_only', 1);
		}
	},
	onload: (frm)=>{
		apply_filter(frm)
	},
	employee: (frm)=>{
		load_required_values(frm)
	},
	before_save:function(frm){
		frm.doc.target_item.map(v=>{
			if (v.qty_quality == 'Quality') v.quantity = 0
			else if (v.qty_quality == 'Quantity') v.quality = 0
			else{
				v.quality = v.quantity = 0
			}
			// frm.refresh_field('target_item')
		})
	}
});

cur_frm.cscript.approver = function(doc){
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

frappe.ui.form.on('Performance Target Evaluation',{
	weightage:(frm)=>{
		frappe.call({
			method: 'calculate_total_weightage',
			doc: frm.doc,
			callback: ()=> {
				frm.refresh_field('total_weightage');
			}
		})
	},
	qty_quality:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		if (row.qty_quality == 'Quality'){
			cur_frm.fields_dict.target_item.grid.toggle_reqd("quality", true)
			cur_frm.fields_dict.target_item.grid.toggle_reqd("quantity", false)
		}else if (row.qty_quality == 'Quantity'){
			cur_frm.fields_dict.target_item.grid.toggle_reqd("quality", false)
			cur_frm.fields_dict.target_item.grid.toggle_reqd("quantity", true)
		}else{
			cur_frm.fields_dict.target_item.grid.toggle_reqd("quality", false)
			cur_frm.fields_dict.target_item.grid.toggle_reqd("quantity", false)
		}
	}
})

frappe.ui.form.on('Common Target Item',{
	reference:(frm,cdt,cdn)=>{
		frappe.call({
			method: 'calculate_total_weightage',
			doc: frm.doc,
			callback: ()=> {
				frm.refresh_field('total_weightage');
			}
		})
	}
})

var load_required_values = (frm)=>{
	if ( !frm.doc.__islocal || frm.doc.docstatus == 1) return
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "PMS Setting",
			fieldname:['max_weightage_for_target','max_no_of_target','min_weightage_for_target','min_no_of_target']
		},
		callback(r) {
			if (r.message){
				frm.set_value('max_weightage_for_target',r.message.max_weightage_for_target)
				frm.set_value('min_weightage_for_target',r.message.min_weightage_for_target)
				frm.set_value('max_no_of_target',r.message.max_no_of_target)
				frm.set_value('min_no_of_target',r.message.min_no_of_target)
				frm.refresh_fields()
			}
		}
	});
}

var add_btn = (frm)=>{
	if ( frm.doc.docstatus == 1 ){
		frm.add_custom_button(__('Create Review'), ()=>{
			frappe.model.open_mapped_doc({
				method: "erpnext.pms.doctype.target_set_up.target_set_up.create_review",	
				frm: cur_frm
			});
		}).addClass("btn-primary custom-create custom-create-css");
	}
}

var hr_add_btn = (frm)=>{
	if (frm.doc.workflow_state == "Waiting Approval" && frappe.user.has_role(['HR Manager', 'HR User'])){
		frm.add_custom_button(__('Manual Approval'), ()=>{
			frappe.call({
				method: "erpnext.pms.doctype.target_set_up.target_set_up.manual_approval_for_hr",
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
		}).addClass("btn-primary");
	}
}

var apply_filter=(frm)=> {
	cur_frm.set_query('pms_calendar', ()=> {
		return {
			'filters': {
				'name': frappe.defaults.get_user_default('fiscal_year'),
				'docstatus': 1
			}
		};
	});
}
frappe.form.link_formatters['Employee'] = function(value, doc) {
	return value
}