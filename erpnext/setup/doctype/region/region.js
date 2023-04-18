// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Region', {
	refresh: function(frm) {
		frm.add_custom_button("Pull Branch",function(){
			frappe.call({
				method:'get_branch',
				doc:frm.doc,
				callback:function(r){
					frm.refresh_fields('items')
					frm.dirty()
				},
				freeze: true,
				freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Please Wait...</span>',
			})
		})
	}
});
