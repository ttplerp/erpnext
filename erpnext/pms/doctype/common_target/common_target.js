// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Common Target', {
	// refresh: function(frm) {

	// }
	pms_calendar:(frm)=>{
		load_required_values(frm)
	}
});

var load_required_values = (frm)=>{
	if ( !frm.doc.__islocal || frm.doc.docstatus == 1) return
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "PMS Setting",
			fieldname:['max_weightage_for_target','min_weightage_for_target']
		},
		callback(r) {
			if (r.message){
				frm.set_value('max_weightage_for_target',r.message.max_weightage_for_target)
				frm.set_value('min_weightage_for_target',r.message.min_weightage_for_target)
				frm.refresh_fields()
			}
		}
	});
}