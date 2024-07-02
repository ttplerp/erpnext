// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Pay Slip', {
	refresh: function(frm) {
		if(frm.doc.docstatus===1){
			frm.add_custom_button(__('Ledger'), function(){
				frappe.route_options = {
                    voucher_no: frm.doc.name,
                    from_date: frm.doc.posting_date,
                    to_date: frm.doc.posting_date,
                    company: frm.doc.company,
                    group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			},__('View'));
        }
	},

	get_attendance: function (frm) {
		if (frm.doc.docstatus != 1) {
			frappe.call({
				method: "get_desuup_attendance",
				doc: frm.doc,
				callback: function (r) {
					frm.refresh_field("attendances")
					frm.refresh_field("total_days_present")
					frm.dirty()
				}
			})
		}
	},

	month_name: function (frm) {
		frm.events.clear_items_table(frm);
		frm.call({
			doc: frm.doc,
			method: "set_month_dates",
			callback: function(r) {
				frm.refresh_field("start_date");
				frm.refresh_field("end_date");
			},
		})
	},

	clear_items_table: function (frm) {
		frm.clear_table('attendances');
		frm.refresh();
	},
});
