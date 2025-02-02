// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Approver Settings', {
	onload: function(frm) {
        frm.fields_dict["supervisors"].grid.get_field("branch").get_query = function(doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            return {
                filters: {
                    "company": child.company
                }
            };
        };

		frm.fields_dict["managers"].grid.get_field("branch").get_query = function(doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            return {
                filters: {
                    "company": child.company
                }
            };
        };
    },

	refresh: function(frm) {
		frm.set_query("document_type", function(doc){
			return {
				filters: {
					'is_submittable': 1
				}
			}
		})
	}
});
