// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deployment Withdrawal', {
	get_desuups: function(frm) {
		if(frm.doc.deployment){
			return frappe.call({
				method: "get_desuups",
				doc: frm.doc,
				callback: function(r, rt) {
					frm.refresh_field("items");
					frm.refresh_fields();
				},
				freeze: true,
				freeze_message: "Loading details .... Please Wait"
			});
		}else{
			frappe.throw("Deployment reference is missing. ")
		}
	},
});
