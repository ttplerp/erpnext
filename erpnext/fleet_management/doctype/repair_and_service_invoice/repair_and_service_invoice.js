// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Repair And Service Invoice', {
	onload: function (frm) {
		let grid = frm.fields_dict['advances'].grid;
        grid.cannot_add_rows = true;
	},
	refresh: function(frm) {
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.add_custom_button(__("Get Advance"), function () {
				frm.events.get_advance_details(frm);
			}).toggleClass("btn-primary", !(frm.doc.employees || []).length);
		}

		if (frm.doc.docstatus == 1){
			cur_frm.add_custom_button(__('Ledger'), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
				
			})
			if (doc.outstanding_amount > 0){
				cur_frm.add_custom_button(__('Pay'), function(doc) {
					frm.events.make_payment_entry(frm)
				})
			}			
		}
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

	get_advance_details: function (frm) {
		return frappe
			.call({
				doc: frm.doc,
				method: "fill_advance_details",
				freeze: true,
				freeze_message: __("Fetching Advanes "),
			})
			.then((r) => {
				if (r.docs?.[0]?.advances) {
					frm.dirty();
					frm.save();
				}
				frm.refresh();
				frm.scroll_to_field("advances");
			});
	},

	make_payment_entry:function(frm){
		frappe.call({
			method:"erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry",
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
				party_type:frm.doc.party_type
			},
			callback: function (r) {
				var doc = frappe.model.sync(r.message);
				frappe.set_route("Form", doc[0].doctype, doc[0].name);
			},
		});
	},
	party_type:function(frm){
		frm.set_value("party","")
		frm.refresh_field("party")
	},
});

frappe.ui.form.on('Repair And Services Invoice Item', {
	rate:function(frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn)
	},
	qty:function( frm, cdt, cdn){
		calculate_amount(frm, cdt, cdn)
	}
})
var calculate_amount = (frm,cdt,cdn)=>{
	var item = locals[cdt][cdn]
	if (item.qty && item.rate){
		item.charge_amount = item.qty * item.rate 
		cur_frm.refresh_field('items')
	}
}
