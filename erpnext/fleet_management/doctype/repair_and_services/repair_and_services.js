// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Repair And Services', {
	refresh: function(frm) {
		frm.set_query("equipment", function (doc) {
			return {
				filters: {
					'branch': doc.branch,
				}
			}
		});

		frm.set_query("item_code", "items", function(){
			return {
				filters: {
					is_fixed_asset: 0,
					is_pol_item: 0,
				}
			}
		});

		if(frm.doc.docstatus == 1) {
			frm.add_custom_button("Request Material", function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.fleet_management.doctype.repair_and_services.repair_and_services.make_mr",
					frm: cur_frm
				});
			},__("Create"));
		}
	},

	party_type: function(frm) {
		frm.set_value("party","")
		frm.refresh_field("party")
	},

	tds_percent:function(frm){
		if (frm.doc.tds_percent){
			frappe.call({
				method: "erpnext.accounts.utils.get_tds_account",
				args: {
					percent:frm.doc.tds_percent,
					company:frm.doc.company
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("tds_account", r.message)
						frm.refresh_fields("tds_account")
						frm.set_value("tds_amount", parseFloat(frm.doc.total_amount) * (parseFloat(frm.doc.tds_percent) / 100));
						frm.set_value("outstanding_amount", parseFloat(frm.doc.outstanding_amount) - parseFloat(frm.doc.tds_amount));
					}
				}
			});
		}
	},

});

frappe.ui.form.on('Repair And Services Item', {
	rate:function(frm,cdt,cdn){
		calculate_amount(frm,cdt,cdn)
	},
	qty:function(frm,cdt,cdn){
		calculate_amount(frm,cdt,cdn)
	},
	warehouse:function(frm,cdt,cdn){
		let d = locals[cdt][cdn]
		if (d.warehouse && d.maintain_stock){
			frm.call({
				method: "erpnext.stock.get_item_details.get_bin_details",
				args: {
					item_code:d.item_code,
					warehouse:d.warehouse,
					company:frm.doc.company
				},
				callback:function(r){
					d.actual_qty = r.message.actual_qty
					frm.refresh_field("items")
				}
			})
		}
	}
});

var calculate_amount = (frm,cdt,cdn)=>{
	var item = locals[cdt][cdn]
	if (item.qty && item.rate){
		item.charge_amount = item.qty * item.rate 
		cur_frm.refresh_field('items')
	}
}