// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Management', {
	// refresh: function(frm) {
	// 	console.log("hihih");
	// },
	onload: function(frm){
	
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