// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Prepare Audit Plan', {
	setup: function(frm){
		frm.get_field('audit_checklist').grid.editable_fields = [
			{fieldname: 'type_of_audit', columns: 3},
			{fieldname: 'audit_criteria', columns: 3},
			{fieldname: 'audit_area_checklist', columns: 4},
		];
	},

	refresh: function(frm) {
		add_button_ea(frm)
		add_button_cel(frm)
	},

	onload: function(frm) {		
		apply_filter(frm)

		// frm.set_query("employee", "audit_team", function(doc, cdt, cdn) {
		// 	return {
		// 		filters: {
		// 			branch:'Internal Audit',
		// 		}
		// 	};
		// });
	},

	branch: (frm)=>{
		frm.set_value("supervisor_id",null);
		frm.set_value("supervisor_name",null);
		frm.set_value("supervisor_designation",null);
		get_audit_checklist(frm)
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
		} else{
			frm.set_value("from_date",null);
			frm.set_value("to_date",null);
		}
	}
});

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
