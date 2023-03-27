// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sales Target', {
	refresh: function(frm) {
		cur_frm.set_query("item_sub_group", function() {
			return {
				"filters": {
					"parent_item_group": "Mines Product",
					"is_sub_group":1
				}
			};
		});
	},
	item_sub_group:function(frm){
		frm.events.get_months(frm)
		frm.clear_table("items");
		frm.refresh_field("items")
	},
	fiscal_year:function(frm){
		frm.events.get_months(frm)
	},
	get_months:function(frm){
		frappe.call({
			method:"get_months",
			doc:frm.doc,
			callback:function(r){
				frm.doc.targets = []
				$.each(r.message, function(_i, e){
					let target 			= frm.add_child("targets");
					target.month 		= e.month;
					target.month_no 	= e.month_no;
					target.target_qty 	= e.target_qty
					target.uom 			= e.uom
					target.from_date 	= e.from_date
					target.to_date 		= e.to_date
				})
				frm.refresh_field("targets")
			}
		})
	},
	get_item:function(frm){
		frappe.call({
			method:"get_item",
			doc:frm.doc,
			callback:function(r){
				frm.doc.items = []
				$.each(r.message, function(_i, e){
					let item = frm.add_child("items");
					item.item_code = e.item_code
					item.item_name = e.item_name
					item.item_sub_group = e.item_sub_group
					item.item_group = e.item_group
				})
				frm.refresh_field("items")
			}
		})
	}
});

frappe.ui.form.on('Sales Target Item', {
	target_qty:function(frm){
		calculate_total_qty(frm)
	}
})
var calculate_total_qty = function(frm){
	let total_qty = 0
	$.each(frm.doc.targets, function(_i,e){
		total_qty += flt(e.target_qty)
	})
	frm.set_value("total_target_qty",total_qty)
	frm.refresh_field("total_target_qty")
}