// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuung Sales', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
			cur_frm.add_custom_button(__("Stock Ledger"), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company
				};
				frappe.set_route("query-report", "Stock Ledger");
			}, __("View"));

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
	onload: function(frm) {
		frm.set_query("from_warehouse", function (doc) {
			return {
				// filters: { 'company': doc.company }
				query: "erpnext.controllers.queries.filter_branch_warehouse",
				filters: { 'company': frm.doc.company, "branch": frm.doc.branch}
			};
		});
	}
});


frappe.ui.form.on("Desuung Sales", "onload", function (frm) {
	frm.set_query("item_code", "items", function () {
		return {
			"filters": {
				"item_group": "Sales Product"
			}
		};
	});
});

frappe.ui.form.on('Sales Order Item', {
	item_code: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		get_selling_price(frm, row);
	},
	qty: function (frm, cdt, cdn) {
		var i = locals[cdt][cdn];
		if (i.rate) {
			frappe.model.set_value(cdt, cdn, "amount", flt(i.rate) * flt(i.qty))
		}
	},
	rate: function (frm, cdt, cdn) {
		var i = locals[cdt][cdn];
		if (i.qty) {
			frappe.model.set_value(cdt, cdn, "amount", flt(i.rate) * flt(i.qty))
		}
	},
	amount: function(frm, cdt, cdn) {
		var total = 0;
		frm.doc.items.forEach(function(d) {total += d.amount});
		frm.set_value("total", total)
	},
	items_remove: function (frm, cdt, cdn) {
		var total = 0;
		frm.doc.items.forEach(function(d) {total += d.amount});
		frm.set_value("total", total)
	}
});

function get_selling_price(frm, row) {
	frappe.call({
		method: "get_selling_price",
		doc: cur_frm.doc,
		args: { 'item_code': row.item_code, 'branch': cur_frm.doc.branch, 'posting_date': cur_frm.doc.posting_date },
		callback: function (r) {
			if (r.message) {
				console.log(r.message)
				frappe.model.set_value(row.doctype, row.name, "price_template", r.message[0]['name']);
				frappe.model.set_value(row.doctype, row.name, "price_list_rate", r.message[0]['selling_price']);
				frappe.model.set_value(row.doctype, row.name, "rate", r.message[0]['selling_price']);
			}
		}
	})
}