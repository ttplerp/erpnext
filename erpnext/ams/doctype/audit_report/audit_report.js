// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Audit Report', {
	get_audit_checklist: (frm) => {
		if (frm.doc.execute_audit_no) {
			frappe.call({
				method: 'get_audit_checklist',
				doc: frm.doc,
				callback:  () =>{
					frm.refresh_field("audit_checklist");
				}
			})
		}else{
			frappe.throw("Required Execute Audit No.>")
		}
	},
});

frappe.ui.form.on("Audit Report Checklist Item", {
	form_render: function(frm, cdt, cdn){
		var item = locals[cdt][cdn];
		var nature_of_irreg = frappe.meta.get_docfield("Audit Report Checklist Item","nature_of_irregularity", cur_frm.doc.name)
		var status = frappe.meta.get_docfield("Audit Report Checklist Item","status", cur_frm.doc.name);		
		var audit_r = frappe.meta.get_docfield("Audit Report Checklist Item","audit_remarks", cur_frm.doc.name);
		var auditee_r = frappe.meta.get_docfield("Audit Report Checklist Item","auditee_remarks", cur_frm.doc.name);
		frappe.call({
			method: "get_auditor_and_auditee",
			doc: frm.doc,
			callback: function(r){
				if(item.status == "Closed"){
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', false);
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', false);
					status.read_only = 1;
					audit_r.read_only = 1;
					auditee_r.read_only = 1;
					nature_of_irreg.read_only = 1;
					audit_r.reqd = 0;
					auditee_r.reqd = 0;
				}else if(item.status == "Open"){
					status.read_only = 1;
					if(r.message[0]==1){
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', true);
					}
					else{
						frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', false);
					}
					if(r.message[1]==1){
						auditee_r.read_only = 0;
						frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', true);
					}
					else{
						frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', false);
					}
					nature_of_irreg.read_only = 1;
				}
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
				else{
					status.read_only = 1;
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('audit_remarks', false);
					frm.fields_dict['audit_checklist'].grid.grid_rows_by_docname[cdn].toggle_editable('auditee_remarks', false);
				}
			}
		})

		frm.refresh_fields("audit_checklist");
	},
});

