// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("project", "branch","branch");
cur_frm.add_fetch("project", "cost_center","cost_center");
cur_frm.add_fetch("boq", "boq_type", "boq_type");
		
frappe.ui.form.on('BOQ Addition', {
	setup: function(frm){
		frm.get_field('boq_item').grid.editable_fields = [
                        { fieldname: 'boq_code', columns: 1 },
                        { fieldname: 'item', columns: 3 },
                        { fieldname: 'is_group', columns: 1 },
                        { fieldname: 'uom', columns: 1 }, 
                        { fieldname: 'quantity', columns: 1 },
                        { fieldname: 'rate', columns: 1 },
                        { fieldname: 'amount', columns: 2 }
                ];
	
	},
	
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
	},
	
	project: function(frm){
		frm.trigger("get_defaults");
	},
	
	boq: function(frm){
		frm.add_fetch("boq", "boq_type", "boq_type");
	},
	
	get_defaults: function(frm){
		frm.add_fetch("project", "branch","branch");
		frm.add_fetch("project", "cost_center","cost_center");		
	},
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

        //if(child.quantity && child.rate){
        amount = parseFloat(child.quantity) * parseFloat(child.rate)
       	//}

        frappe.model.set_value(cdt, cdn, 'amount', parseFloat(amount));
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
}

