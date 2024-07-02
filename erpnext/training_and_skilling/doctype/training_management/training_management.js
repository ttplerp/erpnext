// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Management', {
	refresh: function(frm) {
		frm.events.make_custom_buttons(frm);
	},
	onload: function(frm){
		
	},

	make_custom_buttons: function (frm) {
		if (frm.doc.status == 'On Going') {
			frm.add_custom_button(__("Mess Advance"), () => frm.events.make_mess_advance(frm), __('Create'));
		}
	},

	make_mess_advance: function (frm) {
		frappe.call({
			method: "make_mess_advance",
			doc: frm.doc,
			freeze: true,
			callback: function(r) {
				if(r.message) {

					let doc = frappe.model.sync(r.message)[0];
					frappe.set_route("Form", doc.doctype, doc.name);
				}
			}
		});
	},
});

cur_frm.fields_dict['trainer_details'].grid.get_field('trainer_id').get_query = function(frm, cdt, cdn) {
	return {
		filters: {
			// "employment_type": 'Contract - DSP',
			"employee_group": 'Trainers - DSP'
		}
	}
}