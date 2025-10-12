// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Audit Report', {
	// get_audit_checklist: (frm) => {
	// 	if (frm.doc.execute_audit_no) {
	// 		frappe.call({
	// 			method: 'get_audit_checklist',
	// 			doc: frm.doc,
	// 			callback:  () =>{
	// 				frm.refresh_field("audit_checklist");
	// 			}
	// 		})
	// 	}else{
	// 		frappe.throw("Required Execute Audit No.>")
	// 	}
	// },

	refresh: function(frm) {
		frappe.call({
			method: "check_auditor_and_audit_report",
			doc: frm.doc,
			callback: function(r){
				// if (frm.doc.docstatus == 1 && (frappe.session.user == frm.doc.owner || r.message[0] == 1)){
				if (frm.doc.docstatus == 1 || (r.message == 1)){
					frm.add_custom_button(__('Create Follow Up'), ()=>{
						frappe.model.open_mapped_doc({
							method: "erpnext.ams.doctype.audit_report.audit_report.create_follow_up",	
							frm: frm
						});
					}).addClass("btn-primary custom-create custom-create-css");
				}
			}
		})
	},

	onload: function(frm) {
		frm.refresh_fields();
		frm.set_query("employee", "direct_accountability", function(doc, cdt, cdn) {
			return {
				filters: {
					branch:cur_frm.doc.branch,
				}
			};
		});
		frm.set_query("supervisor", "supervisor_accountability", function(doc, cdt, cdn) {
			return {
				filters: {
					branch:cur_frm.doc.branch,
				}
			};
		});
	},
	
	get_observation: (frm) => {
		frm.refresh_fields();
		frappe.call({
			method: 'get_observation',
			doc: frm.doc,
			callback: function(r){
				frm.refresh_field("direct_accountability");
				frm.refresh_field('supervisor_accountability');
			}
		})
	}
});

frappe.ui.form.on("Audit Initial Report Checklist Item", {
	form_render: function(frm, cdt, cdn){
		var item = locals[cdt][cdn];
		var nature_of_irreg = frappe.meta.get_docfield("Audit Initial Report Checklist Item","para_title", cur_frm.doc.name)
		var status = frappe.meta.get_docfield("Audit Initial Report Checklist Item","status", cur_frm.doc.name);		
		var audit_r = frappe.meta.get_docfield("Audit Initial Report Checklist Item","audit_remarks", cur_frm.doc.name);
		var auditee_r = frappe.meta.get_docfield("Audit Initial Report Checklist Item","auditee_remarks", cur_frm.doc.name);
		frappe.call({
			method: "get_auditor_and_auditee",
			doc: frm.doc,
			callback: function(r){
				if(["Closed","Resolved"].includes(item.status) && cur_frm.doc.docstatus == 1){
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('status', false);
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', false);
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', false);
					status.read_only = 1;
					audit_r.read_only = 1;
					auditee_r.read_only = 1;
					nature_of_irreg.read_only = 1;
					audit_r.reqd = 0;
					auditee_r.reqd = 0;
				}
				// else if(item.status == "Open"){
				// 	status.read_only = 1;
				// 	if(r.message[0]==1){
				// 	frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', true);
				// 	}
				// 	else{
				// 		frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', false);
				// 	}
				// 	if(r.message[1]==1){
				// 		auditee_r.read_only = 0;
				// 		frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', true);
				// 	}
				// 	else{
				// 		frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', false);
				// 	}
				// 	nature_of_irreg.read_only = 1;
				// }

				// else if(item.status == "Open" && cur_frm.doc.workflow_state == "Waiting for Auditee Remarks"){
				// 	status.read_only = 1;
				// 	audit_r.read_only = 1;
				// 	nature_of_irreg.read_only = 1;
				// }else if(item.status == "Open" && cur_frm.doc.workflow_state == "Waiting for Verification"){
				// 	status.read_only = 0;
				// 	audit_r.read_only = 1;
				// 	auditee_r.read_only = 1;
				// 	nature_of_irreg.read_only = 1;
				// }

				// else{
				// 	status.read_only = 1;
				// 	frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', false);
				// 	frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', false);
				// }
			}
		})

		frm.refresh_fields("audit_checklist");
	},
});

