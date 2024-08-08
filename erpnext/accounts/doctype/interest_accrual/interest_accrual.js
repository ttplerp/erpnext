// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Interest Accrual', {
	refresh: function(frm) {

	},
	treasury_id: function(frm){

	},
	posting_date: function(frm){
		if(frm.doc.posting_date!=undefined&&frm.doc.posting_date!=null){
			frappe.call({
				method: "get_month",
				doc: frm.doc,
				args: {'posting_date': frm.doc.posting_date},
				callback: function(r){
					if(r.message){
						frm.set_value("month", r.message);
						frm.refresh_field("month");
					}
				}
			})
		}
	}
});
