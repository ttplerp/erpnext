// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Depreciation Entry', {
	refresh: function(frm) {
		if(!frm.is_new() && frm.doc.docstatus == 0){
			frm.add_custom_button(__('Get Depreciation Details'), function() {
				frm.events.get_depreciation_details(frm);
			}).addClass('btn-primary');
		}
		
		frm.add_custom_button(__('Depreciation Schedule Report'), function() {
			frappe.route_options = {
				"report_type": "Monthly Summary",
			};
			frappe.set_route("query-report", "Depreciation Schedule Report");
		}, __('View'));

		if(frm.doc.docstatus == 1){
			frm.add_custom_button(__('General Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"company": frm.doc.company,
					"group_by_voucher": 0
				};
				frappe.set_route("query-report", "General Ledger");
			}, __('View'));
		}
	},
	fiscal_year: function(frm){
		reset_details(frm);
	},
	month: function(frm){
		reset_details(frm);
	},
	get_depreciation_details: function(frm){
		if(frm.is_new()){
			frm.save();
		}

		frappe.call({
			doc: frm.doc,
			method: 'get_depreciation_details',
			callback: function(r){
				// frm.save();
				frm.refresh();
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching Transactions.... Please Wait</span>',
		})
	}
});

var reset_details = function(frm){
	frm.set_value("total_noof_assets", null);
	frm.set_value("total_noof_schedules", null);
	frm.set_value("total_depreciation_amount", null);
	cur_frm.clear_table("summary");
	cur_frm.refresh_fields("summary");
}