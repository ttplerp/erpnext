// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Online Order', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.status === 'Ordered') {
			frm.add_custom_button(__('Receive Payment'), function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.selling.doctype.online_order.online_order.receive_payment",
					frm: cur_frm,
				})
			}, __('Create'));
			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}

		if (frm.doc.docstatus === 1 && frm.doc.status === 'Ready for pickup') {
			frm.add_custom_button(__('Deliver'), function () {
				frappe.call({
					method: "erpnext.selling.doctype.online_order.online_order.create_stock_entry",
					args: {
						docname: frm.doc.name
					},
					callback: function(r) {
						if(r.message) {
						   frappe.msgprint(r.message)
						}
						frm.reload_doc();
					}
				})
			}, __('Create'));
			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
	},
});

