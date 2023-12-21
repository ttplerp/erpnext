// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hire Charge Invoice', {
	refresh: function(frm) {
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
			
			if (!frm.doc.post_journal_entry && frm.doc.is_internal_customer == 0 && frm.doc.party_type =="Customer"){
				cur_frm.add_custom_button(__('Make Journal Entry'), function(doc) {
					frm.events.post_journal_entry(frm)
				},__("Create"))
			}
		}
		frm.add_custom_button(__('Bill Report'), function () {
			frappe.route_options = {
					name: frm.doc.name
			};
			frappe.set_route("query-report", "Bill Report");
		}, __("View"));

		frm.add_custom_button(__('Invoice Details'), function () {
			frappe.route_options = {
					name: frm.doc.name
			};
			frappe.set_route("query-report", "Hire Charge Invoice Details");
			}, __("View"));
		
		if (frm.doc.party_type =="Customer") {
			frm.add_custom_button("Make Arrear Invoice", function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.accounts.doctype.hire_charge_invoice.hire_charge_invoice.make_arrear_payment",
					frm: cur_frm
				});
			},__("Create"));
			cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		}
		cur_frm.page.set_inner_btn_group_as_primary(__('View'));
	},
	settle_imprest_advance: function(frm){
		if(frm.doc.settle_imprest_advance == 0 || frm.doc.settle_imprest_advance == undefined){
			frm.set_value("imprest_party", null);
			frm.refresh_field("imprest_party");
		}
	},
	post_journal_entry:function(frm){
		frappe.call({
			method:"post_journal_entry",
			doc:frm.doc,
			callback: function (r) {},
		});
	},

	onload:function(frm){
		frm.fields_dict['deduct_items'].grid.get_field('account').get_query = function(){
			return {
				filters: {is_group:0}
			}
		}
	},

	is_internal_customer: function(frm){
		if (frm.doc.party_type == "Customer"){
			if (frm.doc.is_internal_customer == 1){
				frm.set_query("party", function() {
					return {
						"filters": {
							"customer_group": "Internal",
							"disabled": 0
						}
					}
				})
			}else{
				frm.set_query("party", function() {
					return {
						"filters": {
							"disabled": 0
						}
					}
				})
			}
		}
	},

	party:function(frm){
		if (frm.doc.is_internal_customer == 0){
			if (frm.doc.party){
				frappe.call({
					method: "erpnext.accounts.party.get_party_account",
					args: {
						party_type:frm.doc.party_type,
						party:frm.doc.party,
						company: frm.doc.company,
					}, callback: function(r) {
						if(r.message) {
							frm.set_value("credit_account",r.message)
							frm.refresh_fields("credit_account")
						}
					}
				});
			}
			frm.clear_table("items");
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
						frm.set_value("tds_account",r.message)
						frm.refresh_fields("tds_account")
					}
				}
			});
		}
	},
	get_logbooks: function (frm) {
		frappe.call({
			method: "get_logbooks",
			doc: frm.doc,
			callback: function (r) {
					frm.refresh_fields();
					frm.dirty()
			},
			freeze: true,
			freeze_message: "Fetching Logbooks....."
		});
	},
	tds_percent:function(frm){
		frm.events.calculate_totals(frm)
	},
	calculate_totals:function(frm){
		cur_frm.call({
			method: "calculate_totals",
			doc: frm.doc,
			callback: function (r, rt) {
					frm.refresh_fields();
			},
		});
	}
});
