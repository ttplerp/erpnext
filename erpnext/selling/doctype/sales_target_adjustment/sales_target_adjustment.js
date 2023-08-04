// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Target Adjustment', {
	// refresh: function(frm) {

	// }

}); 
frappe.ui.form.on('Sales Target Adjustment Item', {
	adjusted_amount:function(frm, cdt,cdn){
		calculate_total_qty(frm)
	}
})
var calculate_total_qty = function(frm){
	let total_qty = 0
	$.each(frm.doc.item, function(_i,e){
		total_qty +=flt(e.adjusted_amount)
	})
	frm.set_value("total",total_qty)
	frm.refresh_field("total")
}