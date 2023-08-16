// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('BOQ Adjustment', {
	// refresh: function(frm) {

	// }
    onload:function(frm){
        frm.fields_dict.boq.get_query = function(){
			return {
				filters:{
					'project': frm.doc.project,
					'docstatus': 1
				}
			}
		};
    }
});
frappe.ui.form.on("BOQ Adjustment Item",{	
	adjustment_quantity: function(frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn);
		calculate_total_amount(frm);
	},
	
	adjustment_amount: function(frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn);
		calculate_total_amount(frm);
	},
	
	boq_item_remove: function(frm, cdt, cdn){
		calculate_total_amount(frm);
	}
});

var calculate_amount = function(frm, cdt, cdn){
	let child = locals[cdt][cdn];
	let amount = 0.0;
	
	if(frm.doc.boq_type != "Milestone Based"){
		amount = parseFloat(child.adjustment_quantity)*parseFloat(child.rate);
		frappe.model.set_value(cdt, cdn, 'adjustment_amount', parseFloat(amount));
	}
	else {
		if(child.adjustment_quantity){
			frappe.model.set_value(cdt, cdn, 'adjustment_quantity', 0.0);
		}
	}
	
	if ((parseFloat(child.balance_amount || 0.0)+parseFloat(child.adjustment_amount || 0.0)) < 0) {
		frappe.msgprint("Adjustment beyond available balance is not allowed.");
	}
}

var calculate_total_amount = function(frm){
	let bi = frm.doc.boq_item || [];
	let total_amount = 0.0;
	
	for(let i=0; i<bi.length; i++){
		if (bi[i].amount){
			total_amount += parseFloat(bi[i].adjustment_amount);
		}
	}
	
	cur_frm.set_value("total_amount",parseFloat(total_amount));
}
