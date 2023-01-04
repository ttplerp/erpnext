// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Course', {
	onload: function(frm){
		frm.set_query('domain', function() {
			return {
				filters: {
					"center_category": 'Domain',
					'disabled': 0
				}
			};
		});

		frm.set_query('course', function() {
			return {
				filters: {
					"center_category": 'Course',
					"parent_cost_center":  frm.doc.domain,
					'disabled': 0
				}
			};
		});

		frm.set_query('pre_requisite_course', function() {
			return {
				filters: {
					"domain":  frm.doc.domain,
				}
			};
		});
	},
	// refresh: function(frm) {

	// }

});
