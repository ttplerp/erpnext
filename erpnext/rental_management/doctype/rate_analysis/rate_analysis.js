// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Rate Analysis', {
	// refresh: function(frm) {

	// }
	setup: function(frm) {
		frm.set_query("item_code", "item", function(frm,cdt,cdn) {
			var row = locals[cdt][cdn];
			// var is_service_item = (row.type == 'Service')? 1:0;
			if (row.service_category !== undefined && row.service_category !== '') {
				return {
					filters: [
						["disabled", "=", 0],
						["is_service_item", "=", (row.type == 'Service')? 1:0],
						["item_group", "=", row.service_category]
					]
				}
			}
			return {
				filters: [
					["disabled", "=", 0],
					["is_service_item", "=", (row.type == 'Service')? 1:0]
				]
			}
		});
		frm.set_query("service_category", "item", function(frm,cdt,cdn) {
			return {
				filters: [
					["is_group", "=", 1]
				]
			}
		});
	}
});

frappe.ui.form.on("Rate Analysis Item", {
	"type": function(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "item_code","");
		frappe.model.set_value(cdt, cdn, "item_name","");
		frappe.model.set_value(cdt, cdn, "uom","");
	},
	"item_code": function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.type == 'Service' && !row.price_list) {
			alert("Price list missing")
		}
		
		if (row.type == 'Service'){
			return
		} else if (row.type == 'Item'){
			get_map(frm, cdt, cdn);
		}
	},
	"warehouse": function(frm, cdt, cdn) {
		var c = locals[cdt][cdn];
		if(c.type == "Item"){
			get_map(frm, cdt, cdn);
		}
	},
	"rate": function(frm, cdt, cdn) {
		var c = locals[cdt][cdn];
		if(c.qty){
			frappe.model.set_value(cdt, cdn, "amount", c.rate * c.qty);
			update_amount(frm, cdt, cdn);
		}
	},
	"qty": function(frm, cdt, cdn) {
		var c = locals[cdt][cdn];
		if(c.rate){
			frappe.model.set_value(cdt, cdn, "amount", c.rate * c.qty);
			update_amount(frm, cdt, cdn);
		}
	},
});

function get_map(frm, cdt, cdn) 
{	
	var c = locals[cdt][cdn];
	if(frm.doc.posting_date && c.item_code && c.posting_time && c.warehouse){
		frappe.call({
			method: "erpnext.stock.doctype.stock_reconciliation.stock_reconciliation.get_stock_balance_for",
			args: {
				item_code: c.item_code,
				warehouse: c.warehouse,
				posting_date: frm.doc.posting_date,
				posting_time: c.posting_time
			},
			callback: function(r) {
				frappe.model.set_value(cdt, cdn, "rate", r.message.rate ?? 0.0);
			}
		});
	}
}

function update_amount(frm, cdt, cdn)
{
	var d = locals[cdt][cdn];
	var items = frm.doc.item || [];
	var total_amount = 0;
	var total_base_amount = 0;
	for(var i = 0; i < items.length; i++ ){
		total_base_amount += items[i].amount;
		console.log("Total : " + total_base_amount);
	}
	console.log("test :" + total_base_amount);

	frm.set_value("base_amount", total_base_amount);
	
	if(frm.doc.base_amount > 0){
		var amt1 = 0.05 * frm.doc.base_amount;
		var amt2 = 0.01 * (frm.doc.base_amount + amt1);
		var amt3 = 0.1 * (frm.doc.base_amount + amt1 + amt2);
		frm.set_value("tools_plants", amt1);
		frm.set_value("water_charges", amt2);
		frm.set_value("overhead_cost", amt3);
	}
	frm.set_value("total_amount", frm.doc.base_amount + amt1 + amt2 + amt3);
}
