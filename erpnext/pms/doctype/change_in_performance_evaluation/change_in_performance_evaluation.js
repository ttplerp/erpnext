// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Change In Performance Evaluation', {
	refresh: function(frm) {
		add_btn(frm)
	},
	// setup:(frm)=>{
	// 	frm.set_value('fiscal_year',frappe.defaults.get_user_default('fiscal_year'))
	// 	cur_frm.set_query('fiscal_year', ()=> {
	// 		return {
	// 			'filters': {
	// 				'name': frappe.defaults.get_user_default('fiscal_year')
	// 			}
	// 		};
	// 	});
	// },
	employee:(frm)=>{
		cur_frm.set_query('current_target', ()=> {
			return {
				'filters': {
					'employee':frm.doc.employee,
					'pms_calendar':frm.doc.fiscal_year,
					'docstatus': ["!=", "2"]
					// 'pms_calendar':frappe.defaults.get_user_default('fiscal_year') 
				}
			};
		});
	},
	reason:(frm)=>{
		if (frm.doc.reason == "Change in PMS Group"){
			frm.set_df_property('current_target', 'reqd', 0)
		}
	}
});

var add_btn = (frm)=>{
	if (frm.doc.docstatus == 1 ){
		frm.add_custom_button(__('Create Target'), ()=>{
			frappe.model.open_mapped_doc({
				method: "erpnext.pms.doctype.change_in_performance_evaluation.change_in_performance_evaluation.create_target",	
				frm: cur_frm
			});
		}).addClass("btn-primary custom-create custom-create-css")
		// abc.css(("color", "background"), ("red", "gold"))
	}
}
