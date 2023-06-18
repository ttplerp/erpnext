// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mechanical Payment', {
	refresh: function(frm) {
		frm.set_df_property("expense_account", "reqd", 1);
		frm.toggle_display("expense_account", 1)
		
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
	},
	"tds_amount": function (frm) {
		calculate_totals(frm)
		frm.toggle_reqd("tds_account", frm.doc.tds_amount)
	},

	"tax_withholding_category": function(frm) {
		set_tds_account(frm);
		// calculate_totals(frm);
		cur_frm.set_df_property("tds_account", "reqd", (frm.doc.tax_withholding_category)? 1:0);
	},
});

function set_tds_account(frm) {
	frappe.call({
		method: "get_tds_details",
		doc: frm.doc,
		args: {
			tax_withholding_category: frm.doc.tax_withholding_category
		},
		callback: function(r) {
			if(r.message) {
				frm.set_value("tds_account", r.message.tax_withholding_account);
				cur_frm.refresh_field("tds_account");
				frm.set_value("tds_amount", flt(flt(r.message.tax_withholding_rate * frm.doc.total_amount) / 100, 2) ?? 0.0);
			}
		}
	})
}

function calculate_totals(frm) {
	var net_amount = frm.doc.total_amount - (frm.doc.tds_amount + frm.doc.other_deduction);
	frm.set_value("net_amount", net_amount);
}