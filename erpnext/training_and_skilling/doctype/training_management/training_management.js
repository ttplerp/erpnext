// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Management', {
	// refresh: function(frm) {
	// 	console.log("hihih");
	// },
	onload: function(frm){
		frm.set_query('domain', function() {
			return {
				filters: {
					"center_category": 'Domain',
					'disabled': 0,
					'cost_center_for': 'DSP'
				}
			};
		});

		frm.set_query('course_cost_center', function() {
			return {
				filters: {
					"center_category": 'Course',
					"parent_cost_center":  frm.doc.domain,
					'disabled': 0
				}
			};
		});

		frm.set_df_property("course_cost_center", "read_only", 0);
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