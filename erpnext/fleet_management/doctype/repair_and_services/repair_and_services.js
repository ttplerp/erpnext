// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Repair And Services', {
	// refresh: function(frm) {

	// }
});
frappe.ui.form.on('Repair And Services Item', {
	// refresh: function(frm) {

	// }
	rate:function(frm,cdt,cdn){
		calculate_amount(frm,cdt,cdn)
	},
	qty:function(frm,cdt,cdn){
		calculate_amount(frm,cdt,cdn)
	},
});

var calculate_amount = (frm,cdt,cdn)=>{
	var item = locals[cdt][cdn]
	if (item.qty && item.rate){
		item.charge_amount = item.qty * item.rate 
		cur_frm.refresh_field('items')
	}
}