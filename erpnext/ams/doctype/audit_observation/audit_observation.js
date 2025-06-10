// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Audit Observation', {
	// refresh: function(frm) {

	// },
	supervisor_id: function(frm) {
		if(!frm.doc.supervisor_designation || !frm.doc.supervisor_name){
			frappe.call({
				method: "get_supervisor_details",
				doc: frm.doc,
				// This is a server-side method that fetches the supervisor's detail
				callback: function(r) {
					if(r.message) {
						frm.set_value("supervisor_designation", r.message.designation);
						frm.set_value("supervisor_name", r.message.employee_name);
						frm.set_value("supervisor_email", r.message.user_id);
					}
				}
			});
		}
	}
});

frappe.ui.form.on('Direct Accountability Item I', {
	// refresh: function(frm) {

	// },
	employee: function(frm, cdt, cdn) {
		var row = locals[cdt][cdt];
		if(!row.employee_name || !frm.doc.designation){
			frappe.call({
				method: "get_employee_details",
				doc: frm.doc,
				args: {"employee": row.employee},
				// This is a server-side method that fetches the supervisor's detail
				callback: function(r) {
					if(r.message) {
						frm.set_value("designation", r.message.designation);
						frm.set_value("employee_name", r.message.employee_name);
					}
				}
			});
		}
	},
	supervisor: function(frm, cdt, cdn) {
		var row = locals[cdt][cdt];
		if(!row.supervisor_name || !frm.doc.supervisor_designation){
			frappe.call({
				method: "get_employee_details",
				doc: frm.doc,
				args: {"employee":row.supervisor},
				// This is a server-side method that fetches the supervisor's detail
				callback: function(r) {
					if(r.message) {
						frm.set_value("supervisor_designation", r.message.designation);
						frm.set_value("supervisor_name", r.message.employee_name);
					}
				}
			});
		}
	}
});

cur_frm.fields_dict['audit_team'].grid.get_field('employee').get_query = function(){
	return{
		query: "erpnext.controllers.queries.filter_auditors"
	}
};