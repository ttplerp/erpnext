// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('MB Entry', {
	// onload: function(frm){
	// 	calculate_totals(frm);
	// },
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
	},

	claim_percent: function (frm) {
		cal_entry_qty_for_milestone(frm)
	},
});

frappe.ui.form.on("MB Entry BOQ",{
	form_render:function(frm, cdt, cdn){
		console.log("here "+String(item)+" docstatus: "+String(frm.doc.docstatus))
		var item = locals[cdt][cdn];
		var df = frappe.meta.get_docfield("MB Entry BOQ", "create_details", frm.doc.name);
		if(frm.doc.docstatus == 0 && item.detailed_mb_id == undefined){
			df.hidden = 0;
			frm.refresh_fields();
		}
		else{
			df.hidden = 1;
			frm.refresh_fields();
		}
		console.log(String(df.reqd))
	},
	create_details: function(frm, cdt, cdn){
		make_details(frm, cdt, cdn)
	},
	no: function (frm, cdt, cdn) {
		calculate_entry_quantity(frm, cdt, cdn)
	},
	breath: function (frm, cdt, cdn) {
		calculate_entry_quantity(frm, cdt, cdn)
	},

	height: function (frm, cdt, cdn) {
		calculate_entry_quantity(frm, cdt, cdn)
	},

	length: function (frm, cdt, cdn) {
		calculate_entry_quantity(frm, cdt, cdn)
	},

	entry_quantity: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},

	entry_amount: function (frm) {
		calculate_total_amount(frm);
	},

	// entry_quantity: function(frm, cdt, cdn){
	// 	child = locals[cdt][cdn];
		
	// 	if(child.entry_quantity > child.act_quantity){
	// 		msgprint(__("Invoice Quantity cannot be greater than balance quantity.").format(child.entry_quantity))
	// 	}
		
	// 	//if(child.entry_quantity && child.entry_rate){
	// 	frappe.model.set_value(cdt, cdn, 'entry_amount', (parseFloat(child.entry_quantity)*parseFloat(child.entry_rate)).toFixed(2));
	// 	//}
	// },
	// entry_amount: function(frm, cdt, cdn){
	// 	var child = locals[cdt][cdn];
	// 	var amount = flt(child.entry_quantity || 0.00)*flt(child.entry_rate || 0.00);
		
	// 	if(child.entry_amount > child.act_amount){
	// 		msgprint(__("Invoice Amount cannot be greater than balance amount."));
	// 	} else {
	// 		if(frm.doc.boq_type !== "Milestone Based" && flt(child.amount) != flt(amount)) {
	// 			frappe.model.set_value(cdt, cdn, 'entry_amount', flt(amount));
	// 		}
	// 	}
	// 	calculate_totals(frm);
	// },
	is_selected: function(frm, cdt, cdn){
		calculate_total_amount(frm);
	},
});

var cal_entry_qty_for_milestone = function (frm) {
	frm.doc.mb_entry_boq.forEach(e => {
		e.entry_quantity = (frm.doc.claim_percent/100) * e.act_quantity 
		e.entry_amount = (frm.doc.claim_percent/100) * e.act_quantity * e.entry_rate 
		// console.log(e.entry_quantity);
	});
	frm.refresh_field('mb_entry_boq')
}

var calculate_entry_quantity = function(frm, cdt, cdn) {
	let child = locals[cdt][cdn];
	let quant = child.no * child.height * child.length * child.breath
	frappe.model.set_value(cdt, cdn, 'entry_quantity', parseFloat(quant));
	frm.refresh_field("entry_quantity", cdt, cdn)
}

var calculate_amount = function (frm, cdt, cdn) {
	let child = locals[cdt][cdn];
	let amount = 0.0;

	if (child.entry_quantity > child.act_quantity) {
		msgprint(__("Invoice Quantity cannot be greater than balance quantity.").format(child.entry_quantity))
	}

	amount = parseFloat(child.entry_quantity) * parseFloat(child.entry_rate)

	frappe.model.set_value(cdt, cdn, 'entry_amount', parseFloat(amount));
	frm.refresh_field("entry_amount", cdt, cdn)
}

var calculate_total_amount = function(frm){
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

var make_details =  function (frm, cdt, cdn) { 
	var item = locals[cdt][cdn];
	console.log(item.name)
	frappe.model.open_mapped_doc({
		method: "erpnext.projects.doctype.mb_entry.mb_entry.make_details",
		args: {"item_name": item.item, "uom": item.uom, "child_ref": item.name},
		frm: frm,
		run_link_triggers: true
	});
}

var check_uncheck_all = function(frm){
	var meb =frm.doc.mb_entry_boq || [];

	for(var id in meb){
		frappe.model.set_value("MB Entry BOQ", meb[id].name, "is_selected", frm.doc.check_all);
	}
}
