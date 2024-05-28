// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Execute Audit', {
	onload_post_render: function(frm) {	
		if(frm.doc.docstatus == 1){
			frm.toggle_display("get_audit_team",0);
			frm.toggle_display("get_checklist",0);
		} else{
			frm.toggle_display("get_audit_team",1);
			frm.toggle_display("get_checklist",1);
		}
	},

	refresh: function(frm) {
		if( (frm.doc.workflow_state == 'Waiting for Assignment' && frm.doc.supervisor_email == frappe.session.user) || frm.doc.docstatus == 1){
			frm.set_df_property('get_observation','hidden',0)
			frm.set_df_property('direct_accountability','hidden',0)
			
		} else{
			frm.set_df_property('get_observation','hidden',1)
			frm.set_df_property('direct_accountability','hidden',1)
		}

	if (frm.doc.docstatus == 1 && frm.doc.status == 'Exit Meeting' && frappe.session.user == frm.doc.owner){
			frm.add_custom_button(__('Create Initial Report'), ()=>{
				frappe.model.open_mapped_doc({
					method: "erpnext.ams.doctype.execute_audit.execute_audit.create_initial_report",	
					frm: frm
				});
			}).addClass("btn-primary custom-create custom-create-css");
		}
	},

	onload: function(frm) {
		frm.set_query("employee", "direct_accountability", function(doc, cdt, cdn) {
			return {
				filters: {
					branch:cur_frm.doc.branch,
				}
			};
		});
	},

	get_audit_team: (frm) => {
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

	get_checklist: (frm) => {
		if (frm.doc.prepare_audit_plan_no) {
			frappe.call({
				method: 'get_checklist',
				doc: frm.doc,
				callback:  () =>{
					frm.refresh_field("audit_checklist");
				}
			})
		}else{
			frappe.throw("Required Reference No. to get <b>Checklist</b>")
		}
	},

	get_observation: (frm) => {
		if (frm.doc.prepare_audit_plan_no) {
			frappe.call({
				method: 'get_observation',
				doc: frm.doc,
				callback:  () =>{
					frm.refresh_field("direct_accountability");
				}
			})
		}else{
			frappe.throw("Required Reference No. to get <b>Observation</b>")
		}
	}

});

frappe.ui.form.on("Execute Audit Checklist Item", {
	form_render: function(frm, cdt, cdn){
		var item = locals[cdt][cdn];
		var status = frappe.meta.get_docfield("Execute Audit Checklist Item","status", cur_frm.doc.name);		
		var audit_r = frappe.meta.get_docfield("Execute Audit Checklist Item","audit_remarks", cur_frm.doc.name);
		var auditee_r = frappe.meta.get_docfield("Execute Audit Checklist Item","auditee_remarks", cur_frm.doc.name);

		if(item.status == "Closed" || cur_frm.doc.docstatus == 0 || cur_frm.doc.status != 'Exit Meeting'){
			status.read_only = 1;
			audit_r.read_only = 1;
			auditee_r.read_only = 1;
		// }else if(item.status == "Open"){
		// 	status.read_only = 0;
		// 	audit_r.read_only = 0;
		// 	auditee_r.read_only = 0;
		}else{
			status.read_only = 1;
			audit_r.read_only = 1;
			auditee_r.read_only = 1;
		}
		frm.refresh_fields("audit_checklist");
	},
});

// To validate who can assign accountability
frappe.ui.form.on("Direct Accountability Item", {	
	"employee": function(frm){
		frappe.call({
			method: "validate_accountability_assigner",
			doc: frm.doc,
			callback:  () =>{
				frm.refresh_field("direct_accountability");
			}
		})
	}
});