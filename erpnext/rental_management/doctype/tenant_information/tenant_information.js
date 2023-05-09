// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tenant Information', {
	// refresh: function(frm) {

	// }
	// on_load: function(frm){
	// 	if(frm.doc.__islocal){
			
	// 	}
	// },
	setup: function(frm){
		frm.set_query("flat_no", function(){
			return {
				"filters":[
					["block_no", "=", frm.doc.block_no]
				]
			};
		});

		frm.set_query("tenant_department", function(){
			return {
				"filters": [
					["ministry_agency", "=", frm.doc.ministry_and_agency]
				]
			};
		});
	}
});
