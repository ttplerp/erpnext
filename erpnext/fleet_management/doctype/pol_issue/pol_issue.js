// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('POL Issue', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1 && cint(frm.doc.out_source) == 0) {
			cur_frm.add_custom_button(__('POL Ledger'), function() {
				frappe.route_options = {
					branch: frm.doc.branch,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					equipment: frm.doc.tanker
				};
				frappe.set_route("query-report", "POL Ledger");
			}, __("View"));
		}
		set_equipment_filter(frm)
		if(!frm.doc.__islocal){
			// if(frappe.model.can_read("Project")) {
				if(frm.doc.journal_entry){
					frm.add_custom_button(__('Journal Entry'), function() {
							frappe.route_options = {"name": frm.doc.journal_entry};
							frappe.set_route("List", "Journal Entry");
					}, __("View"));
				}
			// }
		}
		if(frm.doc.docstatus==1) {
			frm.add_custom_button(__('Stock Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": frm.doc.posting_date,
					"company": frm.doc.company,
				};
				frappe.set_route("query-report", "Stock Ledger");
			}, __('View'));
		}
	},
	branch:function(frm){
		set_equipment_filter(frm)
	},
	pol_type: function(frm){
		set_item_rate(frm)
	},
	warehouse: function(frm){
		set_item_rate(frm)
	},
	receive_in_barrel: function(frm){
		set_item_rate(frm)
	}
});
var set_item_rate = function(frm){
	frappe.call({
		method: "get_rate",
		doc: frm.doc,
		callback: function(r){
			if(r.message){
				frm.doc.items.forEach((row)=>{
					row.rate = flt(r.message)
				})
			}
		}
	})
}
var get_item_rate = function(frm){
	var rate = 0
	frappe.call({
		method: "get_rate",
		doc: frm.doc,
		async: false,
		callback: function(r){
			if(r.message){
				rate = flt(r.message)
			}
		}
	})
	return rate
}
cur_frm.set_query("pol_type", function() {
	return {
		"filters": {
		"disabled": 0,
		"is_pol_item":1
		}
	};
});

var set_equipment_filter=function(frm){
	frm.set_query("tanker", function() {
		return {
			query: "erpnext.fleet_management.fleet_utils.get_container_filtered",
			filters:{}
		};
	});
}

frappe.ui.form.on('POL Issue Items', {
	"equipment":function(frm, cdt, cdn){
		let row = locals[cdt][cdn]
		frm.set_query('fuelbook', 'items', function (doc, cdt, cdn) {
			return {
				filters: {
					"equipment": row.equipment
				}
			}
		});
	},
	items_add: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		var rate = get_item_rate(frm)
		frappe.model.set_value(cdt, cdn, "rate", rate);
	}
})