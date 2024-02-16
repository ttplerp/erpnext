// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Transportation and Hire Charge Entry', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 0 && frm.doc.hire_charge_invoice_created == 0) {
			if (!frm.doc.__islocal){
                cur_frm.add_custom_button(__('Hire Charge Invoice'), function(doc) {
                    frm.events.create_hire_charge_invoice(frm)
                },__("Create"))
            }
		}

		if(frm.doc.docstatus == 1 && frm.doc.hire_charge_invoice_submitted == 1){
            cur_frm.add_custom_button(__('Post To Account'), function(doc) {
				frm.events.post_to_account(frm)
			},__("Create"))
		}
	},

	create_hire_charge_invoice: function(frm) {
		frappe.call({
			method: 'create_hire_charge_invoice',
			doc: frm.doc,
			callback:function(r){
                cur_frm.reload_doc()
            },
            freeze: true,
            freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Creating Hire Charge Invoice ...</span>'
		})
	},
	post_to_account:function(frm){
        frappe.call({
            method:"post_to_account",
            doc:frm.doc,
            callback:function(r){
                cur_frm.reload_doc()
            },
            freeze: true,
            freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Posting To account.....</span>'
        
        })
    },
});

frappe.ui.form.on('Transportation and Hire Charge Entry Item', {
	amount: function(frm, cdt, cdn) {
		calculate_tds_amount(frm, cdt, cdn)
	},
	tds_percent: function(frm, cdt, cdn) {
		calculate_tds_amount(frm, cdt, cdn)

		let child = locals[cdt][cdn];
		if (child.tds_percent != 0 || child.tds_percent != ''){
			frappe.call({
				method: "get_tds_account",
				doc: frm.doc,
				args: {
					"tds_percent": child.tds_percent,
				},
				callback: function(r) {
					frappe.model.set_value(cdt, cdn, 'tds_account', r.message)
					frm.refresh_field("tds_account", cdt, cdn)
				}
			})
		}
	},
});

var calculate_tds_amount = function(frm, cdt, cdn) {
	let child = locals[cdt][cdn];
	let tds_amount = child.tds_percent/100 * child.amount
	frappe.model.set_value(cdt, cdn, 'tds_amount', parseFloat(tds_amount))
	frm.refresh_field("tds_amount", cdt, cdn)
}