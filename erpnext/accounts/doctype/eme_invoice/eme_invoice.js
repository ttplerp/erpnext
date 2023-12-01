// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('EME Invoice', {
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
			if ( !frm.doc.journal_entry && !frm.doc.eme_invoice_entry || !frm.doc.journal_entry && frm.doc.arrear_eme_payment){
				cur_frm.add_custom_button(__('Make Journal Entry'), function(doc) {
					frm.events.post_journal_entry(frm)
				},__("Create"))
			}
		}
		frm.add_custom_button(__('EME Bill Report'), function () {
			frappe.route_options = {
					name: frm.doc.name
			};
			frappe.set_route("query-report", "EME Bill Report");
		}, __("View"));

		frm.add_custom_button(__('EME Invoice Details'), function () {
			frappe.route_options = {
					name: frm.doc.name
			};
			frappe.set_route("query-report", "EME Invoice Details");
			}, __("View"));

		frm.add_custom_button("Make Arrear Invoice", function() {
			frappe.model.open_mapped_doc({
				method: "erpnext.accounts.doctype.eme_invoice.eme_invoice.make_arrear_payment",
				frm: cur_frm
			});
		},__("Create"));
		cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
		cur_frm.page.set_inner_btn_group_as_primary(__('View'));
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
	supplier:function(frm){
		if (frm.doc.supplier){
			frappe.call({
				method: "erpnext.accounts.party.get_party_account",
				args: {
					party_type:"Supplier",
					party:frm.doc.supplier,
					company: frm.doc.company,
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("credit_account",r.message)
						frm.refresh_fields("credit_account")
					}
				}
			});
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
