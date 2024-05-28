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