// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('BOQ Substitution', {
	refresh: function(frm){
        frm.set_query("boq_code", "boq_item", function () {
            return {
                filters: {
                    is_service_item:1,
                    disabled:0
                }
            };
        });
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
	
	get_boq_details: function (frm, cdt, cdn) {
        get_boq_list(frm);
    },
	check_all_boq: function (frm) {
        check_uncheck_all(frm);
    }
});

frappe.ui.form.on("BOQ Substitution Item",{	
	quantity: function (frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },
    rate: function (frm, cdt, cdn) {
        calculate_amount(frm, cdt, cdn);
    },

	substitute: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
	},

    amount: function (frm) {
        calculate_total_amount(frm);
    },
    no: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        var quant = child.no * child.coefficient * child.height * child.length * child.breath
        frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
    },
    breath: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        var quant = child.no * child.coefficient * child.height * child.length * child.breath
        frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
    },
    height: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        var quant = child.no * child.coefficient * child.height * child.length * child.breath
        frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
    },
	length: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        var quant = child.no * child.coefficient * child.height * child.length * child.breath
        frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
    },
    coefficient: function (frm, cdt, cdn) {
        var child = locals[cdt][cdn];
        var quant = child.no * child.coefficient * child.height * child.length * child.breath
        frappe.model.set_value(cdt, cdn, 'quantity', parseFloat(quant));
    }
});

var get_boq_list = function (frm) {
    if (frm.doc.boq) {
            frappe.call({
                method: "erpnext.projects.doctype.boq_substitution.boq_substitution.get_boq_list",
                args: {
                        "boq": frm.doc.boq
                },
                callback: function (r) {
                    if (r.message) {
                        cur_frm.clear_table("boq_item");
                        r.message.forEach(function (boq) {
                            var row = frappe.model.add_child(frm.doc, "BOQ Substitution Item", "boq_item");
                            row.boq_item_name = boq['name'];
                            row.boq_code = boq['boq_code'];
                            row.item = boq['item'];
                            row.uom = boq['uom'];
                            row.balance_quantity = boq['balance_quantity'];
                            row.balance_rate = boq['balance_rate'];
                            row.balance_amount = boq['balance_amount'];
                            row.initial_amount = boq['amount'];
                                });
                            cur_frm.refresh();
                        }
                        else {
                            cur_frm.clear_table("boq_item");
                        }
                }
        });
    } else {
        cur_frm.clear_table("boq_item");
    }
}

var check_uncheck_all = function (frm) {
	var boq = frm.doc.boq_item || [];
	for (var id in boq) {
		frappe.model.set_value("BOQ Substitution Item", boq[id].name, "substitute", frm.doc.check_all_boq);
	}
}

var calculate_amount = function (frm, cdt, cdn) {
    var child = locals[cdt][cdn];
    var amount = 0.0;
	var implication_amount  = 0.0;
    if(child.substitute) {
        amount = parseFloat(child.quantity) * parseFloat(child.rate)
        implication_amount = parseFloat(child.amount) - parseFloat(child.initial_amount)
    }

    frappe.model.set_value(cdt, cdn, 'amount', parseFloat(amount));
	frappe.model.set_value(cdt, cdn, 'implication_amount', parseFloat(implication_amount));
}

var calculate_total_amount = function (frm) {
    var bi = frm.doc.boq_item || [];
    var total_amount = 0.0
	var initial_amount = 0.0
	var implication_amount = 0.0

    for (var i = 0; i < bi.length; i++) {
        if (bi[i].amount || bi[i].initial_amount) {
            total_amount += parseFloat(bi[i].amount);
            initial_amount += parseFloat(bi[i].initial_amount);
            implication_amount += parseFloat(bi[i].implication_amount);
        }
    }
    frm.set_value("total_amount", total_amount);
	frm.set_value("initial_amount", initial_amount);
	frm.set_value("implication_amount", implication_amount);
}
