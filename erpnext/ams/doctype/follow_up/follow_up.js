// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Follow Up', {
	onload_post_render: function(frm) {	
		if(frm.doc.docstatus == 1){
			frm.toggle_display("get_direct_accountability",0);
			frm.toggle_display("get_observations",0);
		} else{
			frm.toggle_display("get_direct_accountability",1);
			frm.toggle_display("get_observations",1);
		}
	},
	refresh: function(frm) {
		if (frm.doc.docstatus == 1 && frm.doc.cflg_follow_up == 0 && frm.doc.owner == frappe.session.user) {
			frm.add_custom_button(__('Close Follow Up'), ()=>{
				frappe.model.open_mapped_doc({
					method: "erpnext.ams.doctype.follow_up.follow_up.create_close_follow_up",	
					frm: cur_frm
				});
			}).addClass("btn-primary custom-create custom-create-css");
		}
	},
	onload: function(frm) {		
		frm.set_query('follow_up_by', ()=> {
			return {
				'filters': {
					branch:'Internal Audit',
				}
			};
		});
	
		frm.set_query('execute_audit_no', ()=> {
			return {
				'filters': {
					'status': ['in', ['Initial Report','Follow Up']],
					'docstatus': 1,
					branch: cur_frm.doc.branch,
				}
			};
		});
	},
	get_direct_accountability: (frm) => {
		if (frm.doc.execute_audit_no) {
			frappe.call({
				method: 'get_direct_accountability',
				doc: frm.doc,
				callback:  () =>{
					frm.refresh_field("direct_accountability");
				}
			})
		}else{
			frappe.throw("Required Execute Audit No. to get <b>Employee in Direct Accountability</b>")
		}
	},

	get_observations: (frm) => {
		if (frm.doc.execute_audit_no) {
			frappe.call({
				method: 'get_observations',
				doc: frm.doc,
				callback:  () =>{
					frm.refresh_field("audit_observations");
					frm.refresh_fields()
				}
			})
		}else{
			frappe.throw("Required Execute Audit No. to get <b>Audit Observations</b>")
		}
	},
});

frappe.ui.form.on("Follow Up Checklist Item", {
	form_render: function(frm, cdt, cdn){
		let status = frappe.meta.get_docfield("Follow Up Checklist Item","status", cur_frm.doc.name);		
		let audit_r = frappe.meta.get_docfield("Follow Up Checklist Item","audit_remarks", cur_frm.doc.name);
		let auditee_r = frappe.meta.get_docfield("Follow Up Checklist Item","auditee_remarks", cur_frm.doc.name);
		let user_id = frappe.session.user;
		let supervisor_email = cur_frm.doc.supervisor_email;
		let row = locals[cdt][cdn];
		
		if(user_id == frm.doc.owner && row.status != 'Closed'){
			status.read_only = 1;
			audit_r.read_only = 0;
			auditee_r.read_only = 1;
		}else if(user_id == supervisor_email && row.status != 'Closed'){
			status.read_only = 1;
			audit_r.read_only = 1;
			auditee_r.read_only = 0;
		}else{
			status.read_only = 1;
			audit_r.read_only = 1;
			auditee_r.read_only = 1;
		}

		frm.refresh_fields("audit_checklist");
	}
});