// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('PMS Summary', {
	onload: function(frm) {
		// frm.set_value('pms_calendar',frappe.defaults.get_user_default('fiscal_year'))
		cur_frm.set_query('pms_calendar', ()=> {
			return {
				'filters': {
					'name': frappe.defaults.get_user_default('fiscal_year')
				}
			};
		});
	},
	employee:function(frm){
		get_summary(frm)
	}
});
var get_summary = (frm)=>{
	if (frm.doc.docstatus == 1) return
	if (frm.doc.employee && frm.doc.pms_calendar){
		frappe.call({
			method: 'get_summary',
			doc: frm.doc,
			callback: (r)=> {
				frm.refresh_fields()
			}
		})
	}
}
frappe.form.link_formatters['Employee'] = function(value, doc) {
	return value
}