// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("branch", "cost_center","cost_center");
cur_frm.add_fetch("raw_material","item_name","raw_material_name");

frappe.ui.form.on('Production Settings', {
	refresh: function(frm) {
		
	}
});

frappe.ui.form.on('Production Settings Item', {
	refresh: function(frm) {

	},
	"parameter_type": function(frm, cdt, cdn) {
		
	},
});
