// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Transportation and Hire Charges', {
	onload: function (frm) {
		frm.get_field("material_issue_details").grid.cannot_add_rows = true;
        frm.refresh_field("material_issue_amount");

		frm.fields_dict['deduction_items'].grid.get_field('account').get_query = function(){
			return {
				filters: {is_group:0}
			}
		}
		frm.fields_dict['addition_items'].grid.get_field('account').get_query = function(){
			return {
				filters: {is_group:0}
			}
		}

		frm.set_query("equipment", function(doc) {
			return {
				filters: {
					'equipment_type': doc.equipment_type,
					'branch': doc.branch
				}
			}
		});
    },

	refresh: function(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Ledger'), function () {
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

		if (frm.doc.docstatus == 1 && frm.doc.status != "Paid" && frm.doc.settle_imprest_advance == 0 ){
			cur_frm.add_custom_button(__('Pay'), function(doc) {
				frm.events.make_payment_entry(frm)
			})
		}
	},
	settle_imprest_advance: function(frm){
		if(frm.doc.settle_imprest_advance == 0 || frm.doc.settle_imprest_advance == undefined){
			frm.set_value("imprest_party", null);
			frm.refresh_field("imprest_party");
		}
	},

	party: function(frm){
		frappe.call({
			method: "get_equiment_issue_detail",
			doc: frm.doc,
			callback: function (r) {
					frm.refresh_fields();
					frm.dirty()
			},
		});
	},

	tds_percent:function(frm){
		if (frm.doc.tds_percent){
			frappe.call({
				method: "erpnext.accounts.utils.get_tds_account",
				args: {
					percent: frm.doc.tds_percent,
					company: frm.doc.company,
					party_type: frm.doc.party_type
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("tds_account", r.message)
						frm.refresh_fields("tds_account")
					}
				}
			});
		}
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
	},

	make_payment_entry: function(frm) {
		frappe.call({
			method:"erpnext.fleet_management.doctype.transportation_and_hire_charges.transportation_and_hire_charges.make_payment_entry",
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
				party_type:frm.doc.party_type,
				party:frm.doc.party
			},
			callback: function (r) {
				var doc = frappe.model.sync(r.message);
				frappe.set_route("Form", doc[0].doctype, doc[0].name);
			},
		});
	}
});
