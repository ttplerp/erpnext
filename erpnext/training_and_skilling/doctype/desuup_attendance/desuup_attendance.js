// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.cscript.onload = function(doc, cdt, cdn) {
	if(doc.__islocal) cur_frm.set_value("attendance_date", frappe.datetime.get_today());
}

frappe.ui.form.on('Desuup Attendance', {
	// refresh: function(frm) {

	// },

	items_add: function(frm, cdt, cdn) {
        calculate_total_desuups(frm);
    },
    // Recalculate totals when a row is removed from the items table
    items_remove: function(frm, cdt, cdn) {
        calculate_total_desuups(frm);
    },
    // Recalculate totals when a row field is changed
    items_on_form_rendered: function(frm, cdt, cdn) {
        calculate_total_desuups(frm);
    },
});

function calculate_total_desuups(frm) {
    let total = 0;

    // Loop through each item in the items table
    $.each(frm.doc.items || [], function(i, item) {
        total +=1
    });

    // Update the total fields on the form
    frm.set_value('number_of_desuups', total);
}
