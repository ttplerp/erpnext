// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Equipment Material Issue', {
	setup: function(frm) {
		frm.set_indicator_formatter("item_code", function (doc) {
			if (!doc.s_warehouse) {
				return "blue";
			} else {
				return doc.qty <= doc.actual_qty ? "green" : "orange";
			}
		});
	},

	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
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
		if(frm.doc.docstatus==1) {
			frm.add_custom_button(__('Stock Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": frm.doc.posting_date,
					"company": frm.doc.company,
				};
				frappe.set_route("query-report", "Stock Ledger");
			}, __('View'));
		}

		frm.set_query("supplier", function(){
			return {
				filters: { 'disabled': 0 }
			}
		});

		frm.set_query("warehouse", function (doc) {
			return {
				filters: { 'company': doc.company, 'disabled': 0, 'is_group': 0 }
			};
		});

		frm.set_query('project', function(doc) {
			return {
				filters: {
					"cost_center": doc.cost_center
				}
			};
		});

		frm.set_query('advance_type', function(doc) {
			return {
				filters: {
					"party_type": "Supplier"
				}
			};
		});
	},

	before_save: function (frm) {
		frm.doc.items.forEach((item) => {
			item.uom = item.uom || item.stock_uom;
		});
	},

	company: function (frm) {
		if (frm.doc.company) {
			var company_doc = frappe.get_doc(":Company", frm.doc.company);
			if (company_doc.default_letter_head) {
				frm.set_value("letter_head", company_doc.default_letter_head);
			}
		}
	},

	set_basic_rate: function (frm, cdt, cdn) {
		const item = locals[cdt][cdn];
		item.transfer_qty = flt(item.qty) * flt(item.conversion_factor);

		const args = {
			item_code: item.item_code,
			posting_date: frm.doc.posting_date,
			posting_time: frm.doc.posting_time,
			warehouse: cstr(frm.doc.warehouse),
			// serial_no: item.serial_no,
			// batch_no: item.batch_no,
			company: frm.doc.company,
			qty: -1 * flt(item.qty),
			voucher_type: frm.doc.doctype,
			voucher_no: frm.doc.name,
			// allow_zero_valuation: 1,
		};

		if (item.item_code) {
			frappe.call({
				method: "erpnext.stock.utils.get_incoming_rate",
				args: {
					args: args,
				},
				callback: function (r) {
					frappe.model.set_value(cdt, cdn, "basic_rate", r.message || 0.0);
					frm.events.calculate_basic_amount(frm, item);
				},
			});
		}
	},

	calculate_basic_amount: function (frm, item) {
		item.basic_amount = flt(
			flt(item.transfer_qty) * flt(item.basic_rate),
			precision("basic_amount", item)
		);
		frm.events.calculate_total_amount(frm);
	},

	calculate_total_amount: function (frm) {
		let total = 0
		frm.doc.items.forEach((item) => {
			total += item.basic_amount;
		});

		frm.set_value({total_amount: flt(total), outstanding_amount: flt(total)});
	},
});

frappe.ui.form.on('Equipment Material Issue Item', {
	qty(frm, cdt, cdn) {
		frm.events.set_basic_rate(frm, cdt, cdn);
	},

	conversion_factor(frm, cdt, cdn) {
		frm.events.set_basic_rate(frm, cdt, cdn);
	},

	basic_rate(frm, cdt, cdn) {
		var item = locals[cdt][cdn];
		frm.events.calculate_basic_amount(frm, item);
	},

	uom(doc, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.uom && d.item_code) {
			return frappe.call({
				method: "erpnext.fleet_management.doctype.equipment_material_issue.equipment_material_issue.get_uom_details",
				args: {
					item_code: d.item_code,
					uom: d.uom,
					qty: d.qty,
				},
				callback: function (r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, r.message);
					}
				},
			});
		}
	},

	item_code(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (d.item_code) {
			var args = {
				item_code: d.item_code,
				warehouse: cstr(frm.doc.warehouse),
				transfer_qty: d.transfer_qty,
				// serial_no: d.serial_no,
				// batch_no: d.batch_no,
				// bom_no: d.bom_no,
				// expense_account: d.expense_account,
				// cost_center: d.cost_center,
				// company: frm.doc.company,
				qty: d.qty,
				// voucher_type: frm.doc.doctype,
				// voucher_no: d.name,
				// allow_zero_valuation: 1,
			};

			return frappe.call({
				doc: frm.doc,
				method: "get_item_details",
				args: args,
				callback: function (r) {
					if (r.message) {
						var d = locals[cdt][cdn];
						$.each(r.message, function (k, v) {
							if (v) {
								frappe.model.set_value(cdt, cdn, k, v); // qty and it's subsequent fields weren't triggered
							}
						});
						refresh_field("items");
					}
				},
			});
		}
	},

});
