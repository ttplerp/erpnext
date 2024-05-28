// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Audit Engagement Letter', {
	refresh: function(frm){
		if(frappe.session.user != frm.doc.supervisor_email){
			frm.set_df_property('remarks','read_only',1)
		} else {
			frm.set_df_property('remarks','read_only',0)
		}
	},

	onload_post_render: function(frm) {	
		if(frm.doc.docstatus == 0 && frm.doc.workflow_state == 'Draft'){
			frm.toggle_display("get_audit_team",1);
		} else {
			frm.toggle_display("get_audit_team",0);
		}
	},

	get_audit_team: (frm)=>{
		if (frm.doc.prepare_audit_plan_no) {
			frappe.call({
				method: 'get_audit_team',
				doc: frm.doc,
				callback:  () =>{
					frm.refresh_field("audit_team");
				}
			})
		}else{
			frappe.throw("Required Reference No. to get <b>Audit Team</b>")
		}
	},
});
