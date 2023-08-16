// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
		
frappe.ui.form.on('BOQ Addition', {
	onload: function(frm){
		frm.fields_dict.boq.get_query = function(){
			return {
				filters:{
					'project': frm.doc.project,
					'docstatus': 1
				}
			}
		};
	},
	
	refresh: function(frm) {
		if(!frm.doc.__islocal && frm.doc.project){
			frm.trigger('get_defaults');
		}
		frm.set_query("boq_code", "boq_item", function () {
			return {
				filters: {
					is_service_item:1,
					disabled:0
				}
			};
		});
	},
	
	project: function(frm){
		frm.trigger("get_defaults");
	}
});

frappe.ui.form.on("BOQ Addition Item", {
	quantity: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},
	rate: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},

	amount: function (frm) {
		calculate_total_amount(frm);
	},
	no: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];
		var quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
	},
	breath: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];
		var quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
	},
	height: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];
		var quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
	},
	length: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];
		var quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
	},
	coefficient: function (frm, cdt, cdn) {
		child = locals[cdt][cdn];
		var quant = child.no * child.coefficient * child.height * child.length * child.breath
		frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
	}
})

var calculate_amount = function (frm, cdt, cdn) {
	child = locals[cdt][cdn];
	amount = 0.0;

	amount = parseFloat(child.quantity) * parseFloat(child.rate)

	frappe.model.set_value(cdt, cdn, 'amount', parseFloat(amount));
	frm.refresh("boq_item")
}

var calculate_total_amount = function (frm) {
	var bi = frm.doc.boq_item || [];
	var total_amount = 0.0

	for (var i = 0; i < bi.length; i++) {
		if (bi[i].amount) {
			total_amount += parseFloat(bi[i].amount);
		}
	}
	frm.set_value("total_amount", total_amount);
	frm.refresh_field("total_amount");
}

