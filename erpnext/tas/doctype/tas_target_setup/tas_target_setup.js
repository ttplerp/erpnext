// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('TAS Target Setup', {
	setup: (frm) => {
		frm.set_query("functional_unit", function(doc) {
			return {
				filters: {
					performance_level: frm.doc.performance_level || null
				}
			};
		});

		frm.set_query('tas_calendar', ()=> {
			return {
				'filters': {
					// 'name': frappe.defaults.get_user_default('fiscal_year'),
					'docstatus': 1
				}
			};
		});
	},
	
	refresh: function(frm){
		frm.trigger('add_toolbar_buttons');
	},

	performance_level: function(frm) {
		frm.set_value("functional_unit", null);
		frm.set_value("parent_unit", null);
	},

	is_root_level: function(frm){
		frm.toggle_reqd("functional_unit", !cint(frm.doc.is_root_level));
		frm.toggle_display("functional_unit", !cint(frm.doc.is_root_level));
	},

	add_toolbar_buttons: function(frm){
		if (frm.doc.docstatus == 0){
			frm.add_custom_button(__('Get Targets'),
				function () { 
					if(!frm.doc.functional_unit){
						frappe.throw(__("Please select <b>Functional Unit</b> first"));
					}
					frm.trigger('get_targets');
			});
		}

		if (frm.doc.docstatus == 1){
			frm.add_custom_button(__('Create Review'), ()=>{
				frappe.model.open_mapped_doc({
					method: "pms.tas.doctype.tas_target_setup.tas_target_setup.create_review",	
					frm: cur_frm
				});
			});
		}
	},

	get_targets: function(frm){
		frappe.call({
			method: "pms.tas.doctype.tas_target_setup.tas_target_setup.get_targes",
			args: {
				performance_level: frm.doc.performance_level,
				functional_unit: frm.doc.functional_unit,
				parent_unit: frm.doc.parent_unit
			},
			callback: function(r){
				console.log(r);
			}
		});
	},

	before_workflow_action: (frm) => {
		console.log('before_workflow_action',frm.selected_workflow_action);
		if (frm.selected_workflow_action === "Reject"){
			// frappe.validated = false;
			frm.trigger("make_reason_for_reject");
		}
	},

	make_reason_for_reject: function(frm){
		var dialog = new frappe.ui.Dialog({
            title: __("Reason for Rejected"),
            fields: [
                {	
					"fieldtype": "Small Text", 
					"label": __("Why to reject"),
                    "fieldname": "reason",
                    "reqd": 1,
                }
            ],
			primary_action_label: 'Submit',
			primary_action(values) {
				console.log(values);
				frappe.call({
					method: "set_rejected_reason",
					doc: cur_frm.doc,
					args: {
						"reason": values.reason                
					},
					callback: function (r) {
						console.log(r.message)
						cur_frm.reload_doc();
						show_alert('Reason Updated');
					}
				});
				dialog.hide();
			}
        });
		// dialog.set_primary_action(__('Submit'), function(frm) {
        //     dialog.hide();
        //     var args = dialog.get_values();
        //     console.log(args)
		// 	if (args.reason == ""){
		// 		frappe.validated = false;
		// 		return
		// 	}
        //     frappe.call({
        //         method: "set_rejected_reason",
        //         doc: cur_frm.doc,
        //         args: {
        //             "reason": args.reason                
        //         },
        //         callback: function (r) {
        //             console.log(r.message)
        //             cur_frm.reload_doc();
        //             show_alert('Reason Updated');
        //         }
        //     });
        // });
        
        dialog.show()

		// frappe.prompt([
		// 	{
		// 		fieldtype: 'Small Text',
		// 		reqd: true,
		// 		fieldname: 'reason'
		// 	}],
		// 	function(args){
		// 		validated = true;
		// 		frappe.call({
		// 			method: 'frappe.core.doctype.communication.email.make',
		// 			args: {
		// 				doctype: frm.doctype,
		// 				name: frm.docname,
		// 				subject: format(__('Reason for {0}'), [frm.doc.workflow_state]),
		// 				content: args.reason,
		// 				send_mail: false,
		// 				send_me_a_copy: false,
		// 				communication_medium: 'Other',
		// 				sent_or_received: 'Sent'
		// 			},
		// 			callback: function(res){
		// 				if (res && !res.exc){
		// 					frappe.call({
		// 						method: 'frappe.client.set_value',
		// 						args: {
		// 							doctype: frm.doctype,
		// 							name: frm.docname,
		// 							fieldname: 'remarks',
		// 							value: frm.doc.remarks ?
		// 								[frm.doc.remarks, frm.doc.workflow_state].join('\n') : frm.doc.workflow_state
		// 						},
		// 						callback: function(res){
		// 							if (res && !res.exc){
		// 								frm.reload_doc();
		// 							}
		// 						}
		// 					});
		// 				}
		// 			}
		// 		});
		// 	},
		// 	__('Reason for ') + __(frm.doc.workflow_state),
		// 	__('End as Rejected')
		// )
	}

});

// financial targets
frappe.ui.form.on('Financial Target Item', {
	financial_target_item_remove: function(frm, cdt, cdn){
		update_total_weight(frm);
	},
	weightage: function(frm, cdt, cdn){
		validate_weightage(frm, cdt, cdn);
		update_total_weight(frm);
	},
	but_assign_target: function(frm, cdt, cdn){
		assign_target(frm, cdt, cdn, 'Financial Target');
	}
});

// non financial targets
frappe.ui.form.on('Non Financial Target Item', {
	non_financial_target_item_remove: function(frm, cdt, cdn){
		update_total_weight(frm);
	},
	weightage: function(frm, cdt, cdn){
		validate_weightage(frm, cdt, cdn);
		update_total_weight(frm);
	},
	but_assign_target: function(frm, cdt, cdn){
		assign_target(frm, cdt, cdn, 'Non Financial Target');
	}
});

// common targets
frappe.ui.form.on('Common Target Item', {
	common_target_item_remove: function(frm, cdt, cdn){
		update_total_weight(frm);
	},
	weightage: function(frm, cdt, cdn){
		validate_weightage(frm, cdt, cdn);
		update_total_weight(frm);
	},
	but_assign_target: function(frm, cdt, cdn){
		assign_target(frm, cdt, cdn, 'Common Target');
	}
});

var validate_weightage = function(frm, cdt, cdn){
	let row = locals[cdt][cdn];
	if (flt(row.weightage) <= 0){
		frappe.msgprint(__("Row# {0}: <b>Weightage</b> should be greater than 0 under <b>{1}</b>", [row.idx, cdt]));
	}
}

var update_total_weight = function(frm){
	let total_financial_weight = 0, total_non_financial_weight = 0,
		total_common_weight = 0, total_weight = 0;

	total_financial_weight = frm.doc.financial_target_item.reduce(function(r, i){return r + flt(i.weightage)}, 0);
	total_non_financial_weight = frm.doc.non_financial_target_item.reduce(function(r, i){return r + flt(i.weightage)}, 0);
	total_common_weight = frm.doc.common_target_item.reduce(function(r, i){return r + flt(i.weightage)}, 0);
	total_weight = total_financial_weight + total_non_financial_weight + total_common_weight;

	frm.set_value('total_financial_weight', total_financial_weight);
	frm.set_value('total_non_financial_weight', total_non_financial_weight);
	frm.set_value('total_common_weight', total_common_weight);
	frm.set_value('total_weight', total_weight);
}

var assign_target = function(frm, cdt, cdn, target_category){
	let row = locals[cdt][cdn];

	frappe.call({
		method: 'frappe.client.get_value',
		args: {
			doctype: 'Assign Target',
			filters: {
				'target_reference': row.name,
			},
			fieldname: ['name']
		},
		callback: function (r) {
			if (r.message) {
				frappe.set_route('Form', 'Assign Target', r.message.name);
			} else {
				var doc = frappe.model.get_new_doc('Assign Target');
				doc.company= frm.doc.company;
				doc.tas_calendar = frm.doc.tas_calendar
				doc.tas_target_setup = frm.docname
				doc.target_reference = row.name;
				doc.target_category = target_category;
				doc.performance_level = frm.doc.performance_level
				doc.performance_indicator = row.performance_indicator;
				doc.performance_target = row.performance_target;
				doc.weightage = row.weightage;
				frappe.set_route('Form', 'Assign Target', doc.name);
			}
		}
	});
}