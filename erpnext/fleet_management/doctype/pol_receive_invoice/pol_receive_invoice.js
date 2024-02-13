// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('POL Receive Invoice', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 ) {
			frm.add_custom_button(__("Ledger"), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.entry_date,
					to_date: frm.doc.entry_date,
					company: frm.doc.company,
					group_by_voucher: false,
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
		
		if (frm.doc.docstatus == 1 && frm.doc.status != "Paid"){
			cur_frm.add_custom_button(__('Pay'), function(doc) {
				frm.events.make_payment_entry(frm)
			})
		}
	},



	make_payment_entry: function(frm) {
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
	}
});
