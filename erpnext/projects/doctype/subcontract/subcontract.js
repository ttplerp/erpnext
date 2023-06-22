// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Subcontract', {
	refresh: function(frm) {
        if(!frm.doc.__islocal && frm.doc.docstatus==1){
			if(frappe.model.can_read("Subcontract Adjustment")) {
				frm.add_custom_button(__("Adjustments"), function() {
					frappe.route_options = {"subcontract": frm.doc.name}
					frappe.set_route("List", "Subcontract Adjustment");
				}, __("View"), true);
			}
			
			frm.add_custom_button(__("Advance"), function(){frm.trigger("make_subcontract_advance")},__("Make"), "icon-file-alt");
			
			if(frappe.model.can_read("MB Entry")) {
				frm.add_custom_button(__("MB Entries"), function() {
					frappe.route_options = {"subcontract": frm.doc.name}
					frappe.set_route("List", "MB Entry");
				}, __("View"), true);
			}			
			
			if(frappe.model.can_read("Project Invoice")) {
				frm.add_custom_button(__("Invoices"), function() {
					frappe.route_options = {"subcontract": frm.doc.name}
					frappe.set_route("List", "Project Invoice");
				}, __("View"), true);
			}			
		}
		if(frm.doc.docstatus==1){
			frm.add_custom_button(__("Adjustment"),function(){frm.trigger("make_subcontract_adjustment")},
				__("Make"), "icon-file-alt"
			);
		}
		
		if(frm.doc.docstatus==1 && parseFloat(frm.doc.claimed_amount) < (parseFloat(frm.doc.total_amount)+parseFloat(frm.doc.price_adjustment))){
			frm.add_custom_button(__("Measurement Book Entry"),function(){frm.trigger("make_book_entry")},
				__("Make"), "icon-file-alt"
			);
			frm.add_custom_button(__("Invoice"),function(){frm.trigger("make_mb_invoice")},
				__("Make"), "icon-file-alt"
			);			
		}
	},
    make_subcontract_adjustment: function(frm){
        // console.log("make subcontract adjustment")
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.subcontract.subcontract.make_subcontract_adjustment",
			frm: frm
		});
	},
	
	make_direct_invoice: function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.subcontract.subcontract.make_direct_invoice",
			frm: frm
		});
	},
		
	make_mb_invoice: function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.subcontract.subcontract.make_mb_invoice",
			frm: frm
		});
	},	
	
	make_book_entry: function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.subcontract.subcontract.make_book_entry",
			frm: frm
		});
	},
	
	project: function(frm){
		frm.trigger("get_defaults");
	},
	
	get_defaults: function(frm){
		frm.add_fetch("project", "branch","branch");
		frm.add_fetch("project", "cost_center","cost_center");		
	},
	
	make_subcontract_advance: function(frm){
		frappe.model.open_mapped_doc({
			method: "erpnext.projects.doctype.subcontract.subcontract.make_subcontract_advance",
			frm: frm
		});
	},
	
	check_all: function(frm){
		check_uncheck_all(frm);
	}
});

frappe.ui.form.on("Subcontract Item",{
	quantity: function(frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn);
	},
	
	rate: function(frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn);
	},
	
	amount: function(frm, cdt, cdn){
		calculate_total_amount(frm);
	},
	
	is_selected: function(frm, cdt, cdn){
		calculate_total_amount(frm);
	},
	
	boq_item_remove: function(frm, cdt, cdn){
		calculate_total_amount(frm);
	},
})

var calculate_amount = function(frm, cdt, cdn){
	let child = locals[cdt][cdn];
	let amount = 0.0;
	
	amount = flt(child.quantity)*flt(child.rate)
	
	frappe.model.set_value(cdt, cdn, 'amount', flt(amount));
	frappe.model.set_value(cdt, cdn, 'balance_quantity', flt(child.quantity));
	frappe.model.set_value(cdt, cdn, 'balance_rate', flt(child.rate));
	frappe.model.set_value(cdt, cdn, 'balance_amount', flt(amount));
}

var calculate_total_amount = function(frm){
	var bi = frm.doc.boq_item || [];
	var total_amount = 0.0, balance_amount = 0.0;
	var amount = 0;
	for(var i=0; i<bi.length; i++){
		if (bi[i].is_selected && bi[i].amount){
			total_amount += flt(bi[i].amount);
		}
	}
	balance_amount = flt(total_amount) - flt(frm.doc.received_amount)
	cur_frm.set_value("total_amount",total_amount);
	cur_frm.set_value("balance_amount",balance_amount);
}

var check_uncheck_all = function(frm){
	var meb =frm.doc.boq_item || [];

	for(var id in meb){
		frappe.model.set_value("Subcontract Item", meb[id].name, "is_selected", frm.doc.check_all);
	}
}
