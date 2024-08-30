// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Close Follow Up', {
	setup: function(frm){
		frm.get_field('audit_observations').grid.editable_fields = [
			{fieldname: 'audit_area_checklist', columns: 2},
			{fieldname: 'nature_of_irregularity', columns: 2},
			{fieldname: 'status', columns: 2},
			{fieldname: 'audit_remarks', columns: 2},
			{fieldname: 'auditee_remarks', columns: 2},
		];
	},
	get_observation: function(frm) {
		if (frm.doc.follow_up_no) {	
			return frappe.call({
				method: 'get_checklist',
				doc: frm.doc,
				callback: () => {
					frm.refresh_field('audit_observations');	
					frm.refresh_fields();	
				}
			})
		} else {
			frappe.msgprint('No Checklist found')
		}
	}
});

frappe.ui.form.on("Follow Up Checklist Item", {
	form_render: function(frm, cdt, cdn){
		let audit_r = frappe.meta.get_docfield("Follow Up Checklist Item","audit_remarks", cur_frm.doc.name);
		let auditee_r = frappe.meta.get_docfield("Follow Up Checklist Item","auditee_remarks", cur_frm.doc.name);
		let user_id = frappe.session.user;
		let supervisor_email = cur_frm.doc.supervisor_email;
		let row = locals[cdt][cdn];
		frappe.call({
			method: "get_auditor_and_auditee",
			doc: frm.doc,
			callback: function(r){
				// if(user_id == frm.doc.owner && row.status != 'Closed'){
				// 	status.read_only = 1;
				// 	audit_r.read_only = 0;
				// 	auditee_r.read_only = 1;
				// }else if(user_id == supervisor_email && row.status != 'Closed'){
				// 	status.read_only = 1;
				// 	audit_r.read_only = 1;
				// 	auditee_r.read_only = 0;
				// }else{
				// 	status.read_only = 1;
				// 	audit_r.read_only = 1;
				// 	auditee_r.read_only = 1;
				// }
				if(r.message[0] == 1){
					audit_r.read_only = 0;
					auditee_r.read_only = 1;
				}else if(r.message[1] == 1){
					audit_r.read_only = 1;
					auditee_r.read_only = 0;
				}else{
					audit_r.read_only = 1;
					auditee_r.read_only = 1;
				}
			}
		})
		frm.refresh_fields("audit_checklist");
	}
});