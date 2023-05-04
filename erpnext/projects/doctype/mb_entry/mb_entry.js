// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('MB Entry', {
	onload: function(frm){
		calculate_totals(frm);
	},
	
	onload_post_render: function(frm){
		cur_frm.refresh();
	},
	
	refresh: function(frm, cdt, cdn) {
	},

	make_mb_invoice: function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.mb_entry.mb_entry.make_mb_invoice",
			frm: frm
		});
	},	
	
	check_all: function(frm){
		check_uncheck_all(frm);
	}
});

frappe.ui.form.on("MB Entry BOQ",{
	entry_quantity: function(frm, cdt, cdn){
		child = locals[cdt][cdn];
		
		if(child.entry_quantity > child.act_quantity){
			msgprint(__("Invoice Quantity cannot be greater than balance quantity.").format(child.entry_quantity))
		}
		
		//if(child.entry_quantity && child.entry_rate){
		frappe.model.set_value(cdt, cdn, 'entry_amount', (parseFloat(child.entry_quantity)*parseFloat(child.entry_rate)).toFixed(2));
		//}
	},
	entry_amount: function(frm, cdt, cdn){
		var child = locals[cdt][cdn];
		var amount = flt(child.entry_quantity || 0.00)*flt(child.entry_rate || 0.00);
		
		if(child.entry_amount > child.act_amount){
			msgprint(__("Invoice Amount cannot be greater than balance amount."));
		} else {
			if(frm.doc.boq_type !== "Milestone Based" && flt(child.amount) != flt(amount)) {
				frappe.model.set_value(cdt, cdn, 'entry_amount', flt(amount));
			}
		}
		calculate_totals(frm);
	},
	is_selected: function(frm, cdt, cdn){
		calculate_totals(frm);
	},
});

var calculate_totals = function(frm){
	var me = frm.doc.mb_entry_boq || [];
	var total_entry_amount = 0.00, net_entry_amount =0.00;
	
	if(frm.doc.docstatus != 1)
	{
		for(var i=0; i<me.length; i++){
			if(me[i].entry_amount && me[i].is_selected==1){
				total_entry_amount += parseFloat(me[i].entry_amount);
			}
		}
		
		cur_frm.set_value("total_entry_amount",(total_entry_amount));
		cur_frm.set_value("total_balance_amount",(parseFloat(total_entry_amount || 0)-parseFloat(frm.doc.total_received_amount || 0)));
	}
}

var check_uncheck_all = function(frm){
	var meb =frm.doc.mb_entry_boq || [];

	for(var id in meb){
		frappe.model.set_value("MB Entry BOQ", meb[id].name, "is_selected", frm.doc.check_all);
	}
}
