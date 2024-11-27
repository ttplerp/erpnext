// Copyright (c) 2023, TTPL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Assign Target', {
	refresh: function(frm) {
		frm.fields_dict['items'].grid.get_field('functional_unit').get_query = function() {
			return {
				query : "pms.tas.doctype.assign_target.assign_target.get_dependent_units",
				filters: {
					"performance_level": frm.doc.performance_level || null,
					"show_dependents": cint(frm.doc.show_dependents)
				}
			}
		}		
	},
	target_reference: function(frm){
		console.log('target_reference: ',frm.doc.target_reference);
	}
});
