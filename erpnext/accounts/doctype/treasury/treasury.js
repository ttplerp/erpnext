// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Treasury', {
	refresh: function(frm) {
        frm.dashboard.links_area.body
            .find('.btn-new').each(function(i, el) {
                $(el).hide();
            });
		frappe.call({
			method:"check_date_for_interest",
			doc: frm.doc,
			callback: function(r){
				if(frm.doc.status != "Closed" && r.message == 1){
					cur_frm.add_custom_button(__('Intrest Accrual'), make_interest_accrual, __('Create'));
				}
			}
		})
		frappe.call({
			method:"check_date_for_maturity",
			doc: frm.doc,
			callback: function(r){
				if(frm.doc.status != "Closed" && r.message == 1){
					cur_frm.add_custom_button(__('Maturity'), make_treasury_maturity, __('Create'));
				}
			}
		})
		cur_frm.page.set_inner_btn_group_as_primary(__('Create'));

	},
	principal_amount: function(frm) {
		frm.set_value("total_outstanding", frm.doc.principal_amount)
		frm.refresh_field("total_outstanding")
	},
});

var make_interest_accrual = function () {
	frappe.model.open_mapped_doc({
		method: "erpnext.accounts.doctype.treasury.treasury.make_interest_accrual",
		frm: cur_frm
	})
}
var make_treasury_maturity = function () {
	frappe.model.open_mapped_doc({
		method: "erpnext.accounts.doctype.treasury.treasury.make_treasury_maturity",
		frm: cur_frm
	})
}