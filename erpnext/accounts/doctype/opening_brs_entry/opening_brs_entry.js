// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Opening BRS Entry', {
	refresh: function(frm) {
		frm.fields_dict['details'].grid.get_field('bank_account').get_query = function(){
			return{
				filters: {
					account_type:[ 'in', ['Bank', 'Cash']],
					is_group:0
				}
			}
		};
	},
	// setup: function(frm) {
	// 	frm.get_docfield("details").allow_bulk_edit = 1;
	// },
});

