// Copyright (c) 2023, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('API Setting', {
	// refresh: function(frm) {

	// },
	generate_token: function (frm){
		if(cur_frm.is_dirty()){
			frm.save();
		}
		
		return frappe.call({
			method: "generate_token",
			doc: cur_frm.doc,
			callback: function(r, rt) {
				frm.refresh_fields();
			},
			freeze: true,
			freeze_message: "Generating Bearer Token..... Please Wait"
		});     
	}
});
