// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Annual Audit Plan', {
	onload: function(frm){
		set_default_field_value(frm)
	},
	refresh:function(frm){
		disable_fields(frm)
	},
	fiscal_year: function(frm){
		set_default_field_value(frm)
	}
});

function disable_fields(frm){
	//disable fields after save
		if (frm.doc.docstatus === 1){
			// open_extension(frm)
			cur_frm.set_df_property("q1_start_date", "read_only", 1);
			cur_frm.set_df_property("q1_end_date", "read_only", 1);
			cur_frm.set_df_property("q2_start_date", "read_only", 1);
			cur_frm.set_df_property("q2_end_date", "read_only", 1);
			cur_frm.set_df_property("q3_start_date", "read_only", 1);
			cur_frm.set_df_property("q3_end_date", "read_only", 1);
			cur_frm.set_df_property("q4_start_date", "read_only", 1);
			cur_frm.set_df_property("q4_end_date", "read_only", 1);
		}
	}

function set_default_field_value(frm){
//set default field base on fiscal year
	if ( frm.doc.fiscal_year && frm.doc.docstatus !== 1){
		frm.set_value("q1_start_date",frm.doc.fiscal_year);
		frm.set_value("q1_end_date",new Date(frm.doc.fiscal_year, 3, 0));

		frm.set_value("q2_start_date",frappe.datetime.add_months(frm.doc.fiscal_year,3));
		frm.set_value("q2_end_date",new Date(frm.doc.fiscal_year, 6, 0));
		
		frm.set_value("q3_start_date",frappe.datetime.add_months(frm.doc.fiscal_year,6));
		frm.set_value("q3_end_date",new Date(frm.doc.fiscal_year, 9, 0));		
		
		frm.set_value("q4_start_date",frappe.datetime.add_months(frm.doc.fiscal_year,9));
		frm.set_value("q4_end_date",new Date(frm.doc.fiscal_year, 12, 0));
	}
}

// function open_extension(frm){
// 	//if need to extend open aap extension doc
// 		frm.add_custom_button('<b><span style="color: blue; font-size: 14px;">Extend</span></b>', () => {
// 			frappe.model.open_mapped_doc({
// 				method: "erpnext.ams.doctype.annual_audit_plan.annual_audit_plan.create_aap_extension",	
// 				frm: cur_frm
// 			});
// 		})
// 	}
