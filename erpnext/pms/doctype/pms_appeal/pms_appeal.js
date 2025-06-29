// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('PMS Appeal', {
	pms_calendar: function(frm) {
		cur_frm.set_query("appeal_based_on", function(doc) {
			return {
				'filters': {
					'employee': doc.employee,
					'pms_calendar': doc.pms_calendar,
					'docstatus': 1
				}
			}
		});
	},
});

frappe.ui.form.on('Form I',{
	form_render:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		frappe.meta.get_docfield("Form I", "reason", cur_frm.doc.name).read_only = frm.doc.workflow_state == 'Waiting PERC' || frm.doc.workflow_state == 'Approved By PERC'
		|| frm.doc.workflow_state == 'Waiting CEO Approval' || frm.doc.workflow_state == 'Approved By CEO' || frm.doc.workflow_state == 'Rejected By CEO' ? 1 : 0
		frappe.meta.get_docfield("Form I", "perc_reasons", cur_frm.doc.name).read_only = frm.doc.workflow_state == 'Draft' || (frm.is_new() && frm.is_dirty()) || frm.doc.workflow_state == 'Rejected By PERC' ? 1 : 0
		// frappe.meta.get_docfield("Form I", "perc_reasons", cur_frm.doc.name).read_only = frm.doc.workflow_state == 'Rejected By PERC' ? 1 : 0
		frm.refresh_field('form_i')
	},
});

frappe.ui.form.on('Form II',{
	form_render:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		frappe.meta.get_docfield("Form II", "reason", cur_frm.doc.name).read_only = frm.doc.workflow_state == 'Waiting PERC' || frm.doc.workflow_state == 'Approved By PERC'
		|| frm.doc.workflow_state == 'Waiting CEO Approval' || frm.doc.workflow_state == 'Approved By CEO' || frm.doc.workflow_state == 'Rejected By CEO' ? 1 : 0
		frappe.meta.get_docfield("Form II", "perc_reasons", cur_frm.doc.name).read_only = frm.doc.workflow_state == 'Draft' || (frm.is_new() && frm.is_dirty()) || frm.doc.workflow_state == 'Rejected By PERC' ? 1 : 0
		frm.refresh_field('form_ii')
	},
});

