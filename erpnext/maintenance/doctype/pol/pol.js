// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('POL', {
	onload: function (frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}

		// Ver 2.0 Begins, following code added by SHIV on 28/11/2017
		if(frm.doc.__islocal) {
			frappe.call({
				method: "erpnext.custom_utils.get_user_info",
				args: {"user": frappe.session.user},
				callback(r) {
					cur_frm.set_value("company", r.message.company);
				}
			});
		}
	},
	refresh: function (frm) {
		if (frm.doc.jv) {
			cur_frm.add_custom_button(__('Bank Entries'), function () {
				frappe.route_options = {
					"Journal Entry Account.reference_type": me.frm.doc.doctype,
					"Journal Entry Account.reference_name": me.frm.doc.name,
				};
				frappe.set_route("List", "Journal Entry");
			}, __("View"));
		}

		if (frm.doc.docstatus == 1 && frm.doc.settled_using_imprest == 1) {
			cur_frm.add_custom_button(__('Accounting Ledger'), function () {
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

	"is_disabled": function (frm) {
		cur_frm.toggle_reqd("disabled_date", frm.doc.is_disabled)
	},
	"get_advance":function(frm){
		get_advance(frm)
	},
	"credit_account": function (frm) {
		frappe.model.get_value("Account", frm.doc.credit_account, "account_type", function (d){
			if (d.account_type == 'Payable' || d.account_type == 'Receivable'){
				cur_frm.toggle_display('party_type', 1);
			} else {
				frm.set_value("party_type", "")
				cur_frm.toggle_display('party_type', 0);
			}
			frm.set_value("party", "")
		});
	}
});

// Added by Dawa Tshering on 17/07/2024
frappe.ui.form.on('POL Item', {
	qty: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
		calculate_total_amount(frm);
	},

	rate: function (frm, cdt, cdn) {
		calculate_amount(frm, cdt, cdn);
		calculate_total_amount(frm);
	},
	items_add: function (frm, cdt, cdn) {
        let child = locals[cdt][cdn];
        let stock_uom = frm.doc.stock_uom;
        frappe.model.set_value(child.doctype, child.name, 'uom', stock_uom);
        frm.refresh_field('items');
    }
});

var calculate_amount = function(frm, cdt, cdn) {
	let child = locals[cdt][cdn];
	let amount = child.qty * child.rate
	frappe.model.set_value(cdt, cdn, 'amount', parseFloat(amount));
	frm.refresh_field("amount", cdt, cdn)
}

var calculate_total_amount = function(frm){
	var me = frm.doc.items || [];
	var total_amount = 0.00;
	var total_qty = 0.00;
	
	if(frm.doc.docstatus != 1)
	{
		for(var i=0; i<me.length; i++){
			if(me[i].amount){
				total_amount += parseFloat(me[i].amount);
				total_qty += parseFloat(me[i].qty);
			}
		}
		
		cur_frm.set_value("total_amount", (total_amount));
		cur_frm.set_value("outstanding_amount", (total_amount));
		cur_frm.set_value("qty", (total_qty));
	}
}
// end here

var get_advance = function(frm){
	if (frm.doc.fuelbook && frm.doc.total_amount) {
		frappe.call({
			method: 'get_advance',
			doc: frm.doc,
			callback:  () =>{
				frm.refresh_field('advances')
				cur_frm.refresh_fields()
			}
		})
	}
}

frappe.ui.form.on("POL", "refresh", function (frm) {
	cur_frm.set_query("cost_center", function () {
		return {
			"filters": {
				"is_disabled": 0,
				"is_group": 0
			}
		};
	});

	cur_frm.set_query("equipment", function () {
		return {
			"filters": {
				"is_disabled": 0
			}
		};
	});

	cur_frm.set_query("pol_type", function () {
		return {
			"filters": {
				"disabled": 0,
				"is_pol_item": 1
			}
		};
	});

	cur_frm.set_query("warehouse", function () {
		return {
			query: "erpnext.controllers.queries.filter_branch_wh",
			filters: { 'branch': frm.doc.branch }
		}
	});

	cur_frm.set_query("equipment_warehouse", function () {
		return {
			query: "erpnext.controllers.queries.filter_branch_wh",
			filters: { 'branch': frm.doc.equipment_branch }
		}
	});

	cur_frm.set_query("hiring_warehouse", function () {
		return {
			query: "erpnext.controllers.queries.filter_branch_wh",
			filters: { 'branch': frm.doc.hiring_branch }
		}
	});

})
