// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('API Setting', {
	// refresh: function(frm) {

	// }
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

frappe.ui.form.on("API Setting Item", {
	fetch_data: function(frm, dt, dn) {
		var d = locals[dt][dn];
		var param = 0;
		if(d.param){
			param = d.param
		}
		return frappe.call({
			method: "erpnext.training_and_skilling.doctype.api_setting.api_setting.fetch_data",
			args: {
				name: d.name,
				param: param
			},
			callback: function(r) {
				if(r.message == "success"){
					cur_frm.reload_doc();
					frappe.msgprint("Successfully updated the details from API")
				}
			},
			freeze: true,
			freeze_message: "Fetching Data and Updating..... Please Wait"
		});
	},
});
