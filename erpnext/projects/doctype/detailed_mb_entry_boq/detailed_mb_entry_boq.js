// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Detailed MB Entry BOQ', {
	// refresh: function(frm) {

	// },
});

frappe.ui.form.on('Detailed MB BOQ Item', {
	// refresh: function(frm) {

	// },
	items_add: function(frm, cdt, cdn){
		frappe.call({
			method: "fetch_item_details",
			doc: frm.doc,
			callback: function(r){
				if(r.message){
					frappe.model.set_value(cdt, cdn, "length", r.message[0]);
					frappe.model.set_value(cdt, cdn, "breadth", r.message[1]);
					frappe.model.set_value(cdt, cdn, "height", r.message[2]);
					frm.refresh_fields();
				}
			}
		})
	},
	no: function(frm, cdt, cdn){
		calculate_entry_quantity(frm, cdt, cdn)
	},
	length: function(frm, cdt, cdn){
		calculate_entry_quantity(frm, cdt, cdn)
	},
	breadth: function(frm, cdt, cdn){
		calculate_entry_quantity(frm, cdt, cdn)
	},
	height: function(frm, cdt, cdn){
		calculate_entry_quantity(frm, cdt, cdn)
	},
});

var calculate_entry_quantity = function(frm, cdt, cdn){
	var item = locals[cdt][cdn];
	var entry_qty = 0
	frappe.model.set_value(cdt, cdn, "quantity", flt(flt(item.no)*flt(item.length)*flt(item.breadth)*flt(item.height),2));
	frm.doc.items.forEach((row)  => {
		entry_qty += row.quantity
	})
	frm.set_value("entry_quantity", entry_qty);
	frm.refresh_fields();
}