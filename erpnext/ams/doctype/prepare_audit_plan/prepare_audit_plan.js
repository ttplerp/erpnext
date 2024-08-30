// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Prepare Audit Plan', {
	setup: function(frm){
		frm.refresh_fields()
		frm.get_field('audit_checklist').grid.editable_fields = [
			{fieldname: 'type_of_audit', columns: 3},
			{fieldname: 'audit_criteria', columns: 3},
			{fieldname: 'audit_area_checklist', columns: 4},
		];
		frm.set_query('supervisor_id', function(doc) {
			return {
				filters: {
					"branch": doc.branch				}
			};
		});
	},

	refresh: function(frm) {
		add_button_ea(frm)
	},

	onload: function(frm) {	
		apply_filter(frm)
		frappe.call({
			method: "check_engagement_letter",
			doc: frm.doc,
			callback: function(r){
				if(r.message == 0){
					add_button_cel(frm)
				}
				frm.refresh_fields();
			}
		})
		frm.refresh_fields();
		frm.set_query("employee", "audit_team", function(doc, cdt, cdn) {
			return {
				query: "erpnext.controllers.queries.filter_auditors"
			};
		});
	},
	fiscal_year: function(frm){
		frappe.call({
			method: "get_iain_number",
			doc: frm.doc,
			callback: function(r){
				if(r.message){
					frm.set_value("iain_number", r.message);
					frm.refresh_field("iain_number");
				}
			}
		})
	},
	branch: (frm)=>{
		frm.set_value("supervisor_id",null);
		frm.set_value("supervisor_name",null);
		frm.set_value("supervisor_designation",null);
		get_audit_checklist(frm)
		frappe.call({
			method: "get_iain_number",
			doc: frm.doc,
			callback: function(r){
				if(r.message){
					frm.set_value("iain_number", r.message);
					frm.refresh_field("iain_number");
				}
			}
		})
	},

	frequency: function(frm){
		if( frm.doc.frequency == 'Quarter 1'){
			frm.set_value("from_date",frm.doc.fiscal_year);
			frm.set_value("to_date",new Date(frm.doc.fiscal_year, 3, 0));
		} else if( frm.doc.frequency == 'Quarter 2'){
			frm.set_value("from_date",frappe.datetime.add_months(frm.doc.fiscal_year,3));
			frm.set_value("to_date",new Date(frm.doc.fiscal_year, 6, 0));
		} else if( frm.doc.frequency == 'Quarter 3'){
			frm.set_value("from_date",frappe.datetime.add_months(frm.doc.fiscal_year,6));
			frm.set_value("to_date",new Date(frm.doc.fiscal_year, 9, 0));
		} else if( frm.doc.frequency == 'Quarter 4'){
			frm.set_value("from_date",frappe.datetime.add_months(frm.doc.fiscal_year,9));
			frm.set_value("to_date",new Date(frm.doc.fiscal_year, 12, 0));
		} else if( frm.doc.frequency == 'First Half Year'){
			frm.set_value("from_date",frm.doc.fiscal_year);
			frm.set_value("to_date",new Date(frm.doc.fiscal_year, 6, 0));
		}
		else if( frm.doc.frequency == 'Second Half Year'){
			frm.set_value("from_date",frappe.datetime.add_months(frm.doc.fiscal_year, 6));
			frm.set_value("to_date",new Date(frm.doc.fiscal_year, 12, 0));
		} else{
			frm.set_value("from_date",null);
			frm.set_value("to_date",null);
		}
	}
});

frappe.ui.form.on('PAP Audit Team Item', {
	form_render: function(frm, cdt, cdn){
		let declaration = frappe.meta.get_docfield("PAP Audit Team Item","declaration", cur_frm.doc.name);		
		let row = locals[cdt][cdn];
		if(row.auditor){
			frappe.call({
				method: "check_auditor",
				doc: frm.doc,
				args: {"auditor": row.employee},
				callback: function(r){
					console.log("Here "+String(r.message))
					// if(user_id == frm.doc.owner && row.status != 'Closed'){
					// 	status.read_only = 1;
					// 	audit_r.read_only = 0;
					// 	auditee_r.read_only = 1;
					// }else if(user_id == supervisor_email && row.status != 'Closed'){
					// 	status.read_only = 1;
					// 	audit_r.read_only = 1;
					// 	auditee_r.read_only = 0;
					// }else{
					// 	status.read_only = 1;
					// 	audit_r.read_only = 1;
					// 	auditee_r.read_only = 1;
					// }
					if(r.message == 1){
						frm.fields_dict['audit_team'].grid.grid_rows_by_docname[cdn].toggle_editable('declaration', true);
					}else{
						frm.fields_dict['audit_team'].grid.grid_rows_by_docname[cdn].toggle_editable('declaration', false);
					}
					frm.refresh_field("audit_team");
				}
			})
		}
	
	}
})
var get_audit_checklist=(frm)=>{
	if (frm.doc.branch) {	
		return frappe.call({
			method: 'get_audit_checklist',
			doc: frm.doc,
			callback: () => {
				frm.refresh_field('audit_checklist');	
			}
		})
	} else {
		frappe.msgprint('No Checklist found')
	}
}

// Validating duplicate check in Audit Team
frappe.ui.form.on("PAP Audit Team Item", {	
	"employee": function(frm){
		validate_audit_team(frm);
	}
});

function validate_audit_team(frm){
	frappe.call({
		method: "validate_audit_team",
		doc: frm.doc
	})
}

// Validating duplicate audit role
frappe.ui.form.on("PAP Audit Team Item", {	
	"audit_role": function(frm){
		validate_audit_role(frm);
	}
});

function validate_audit_role(frm){
	frappe.call({
		method: "validate_audit_role",
		doc: frm.doc
	})
}

// To check if there's any duplicate in audit checklist
// frappe.ui.form.on("PAP Checklist Item", {	
// 	"audit_area_checklist": function(frm){
// 		validate_audit_checklist(frm);
// 	}
// });

// function validate_audit_checklist(frm){
// 	frappe.call({
// 		method: "validate_audit_checklist",
// 		doc: frm.doc
// 	})
// }

var apply_filter=(frm)=> {
	// frm.set_query('fiscal_year', ()=> {
	// 	return {
	// 		'filters': {
	// 			'name': frappe.defaults.get_user_default('fiscal_year'),
	// 			'docstatus': 1
	// 		}
	// 	};
	// });

	// frm.set_query('supervisor_id', ()=> {
	// 	return {
	// 		'filters': {
	// 			branch: cur_frm.doc.branch
	// 		}
	// 	};
	// });
}

// Enable and Disable Engagement button
var add_button_cel = (frm)=>{
	if (frm.doc.docstatus == 1 && frm.doc.status == "Pending" && frm.doc.owner == frappe.session.user){
		frm.add_custom_button(__('Create Engagement Letter'), ()=>{
			frappe.model.open_mapped_doc({
				method: "erpnext.ams.doctype.prepare_audit_plan.prepare_audit_plan.create_engagement",	
				frm: cur_frm
			});
		}).addClass("btn-primary custom-create custom-create-css");
	}
}

// Enable and Disable Execute Audit button
var add_button_ea = (frm)=>{
	if (frm.doc.docstatus == 1 && frm.doc.status == "Engagement Letter" && frm.doc.owner == frappe.session.user){
		frm.add_custom_button(__('Create Execute Audit'), ()=>{
			frappe.model.open_mapped_doc({
				method: "erpnext.ams.doctype.prepare_audit_plan.prepare_audit_plan.create_execute_audit",	
				frm: cur_frm
			});
		}).addClass("btn-primary custom-create custom-create-css");
	}
}
