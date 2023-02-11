// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'erpnext/public/js/controllers/buying.js' %};

frappe.provide("erpnext.stock");

frappe.ui.form.on("Purchase Receipt", {
	setup: (frm) => {
		frm.make_methods = {
			'Landed Cost Voucher': () => {
				let lcv = frappe.model.get_new_doc('Landed Cost Voucher');
				lcv.company = frm.doc.company;
				let lcv_receipt = frappe.model.get_new_doc('Landed Cost Purchase Receipt');
				lcv_receipt.receipt_document_type = 'Purchase Receipt';
				lcv_receipt.receipt_document = frm.doc.name;
				lcv_receipt.supplier = frm.doc.supplier;
				lcv_receipt.grand_total = frm.doc.grand_total;
				lcv.purchase_receipts = [lcv_receipt];

				frappe.set_route("Form", lcv.doctype, lcv.name);
			},
		}

		frm.custom_make_buttons = {
			'Stock Entry': 'Return',
			'Purchase Invoice': 'Purchase Invoice'
		};

		frm.set_query("expense_account", "items", function() {
			return {
				query: "erpnext.controllers.queries.get_expense_account",
				filters: {'company': frm.doc.company }
			}
		});

		frm.set_query("taxes_and_charges", function() {
			return {
				filters: {'company': frm.doc.company }
			}
		});

	},
	onload: function(frm) {
		erpnext.queries.setup_queries(frm, "Warehouse", function() {
			return erpnext.queries.warehouse(frm.doc);
		});
	},

	refresh: function(frm) {
		if(frm.doc.company) {
			frm.trigger("toggle_display_account_head");
		}

		if (frm.doc.docstatus === 1 && frm.doc.is_return === 1 && frm.doc.per_billed !== 100) {
			frm.add_custom_button(__('Debit Note'), function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
					frm: cur_frm,
				})
			}, __('Create'));
			frm.page.set_inner_btn_group_as_primary(__('Create'));
		}

		if (frm.doc.docstatus === 1 && frm.doc.is_internal_supplier && !frm.doc.inter_company_reference) {
			frm.add_custom_button(__('Delivery Note'), function() {
				frappe.model.open_mapped_doc({
					method: 'erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_inter_company_delivery_note',
					frm: cur_frm,
				})
			}, __('Create'));
		}

		frm.events.add_custom_buttons(frm);
	},

	add_custom_buttons: function(frm) {
		if (frm.doc.docstatus == 0) {
			frm.add_custom_button(__('Purchase Invoice'), function () {
				if (!frm.doc.supplier) {
					frappe.throw({
						title: __("Mandatory"),
						message: __("Please Select a Supplier")
					});
				}
				erpnext.utils.map_current_doc({
					method: "erpnext.accounts.doctype.purchase_invoice.purchase_invoice.make_purchase_receipt",
					source_doctype: "Purchase Invoice",
					target: frm,
					setters: {
						supplier: frm.doc.supplier,
					},
					get_query_filters: {
						docstatus: 1,
						per_received: ["<", 100],
						company: frm.doc.company
					}
				})
			}, __("Get Items From"));
		}
	},

	company: function(frm) {
		frm.trigger("toggle_display_account_head");
		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
	},

	toggle_display_account_head: function(frm) {
		var enabled = erpnext.is_perpetual_inventory_enabled(frm.doc.company)
		frm.fields_dict["items"].grid.set_column_disp(["cost_center"], enabled);
	},
});

erpnext.stock.PurchaseReceiptController = class PurchaseReceiptController extends erpnext.buying.BuyingController {
	setup(doc) {
		this.setup_posting_date_time_check();
		super.setup(doc);
	}

	refresh() {
		var me = this;
		// super.refresh();
		if(this.frm.doc.docstatus > 0) {
			this.show_stock_ledger();
			//removed for temporary
			this.show_general_ledger();

			this.frm.add_custom_button(__('Asset'), function() {
				frappe.route_options = {
					purchase_receipt: me.frm.doc.name,
				};
				frappe.set_route("List", "Asset");
			}, __("View"));

			this.frm.add_custom_button(__('Asset Movement'), function() {
				frappe.route_options = {
					reference_name: me.frm.doc.name,
				};
				frappe.set_route("List", "Asset Movement");
			}, __("View"));
		}

		if(!this.frm.doc.is_return && this.frm.doc.status!="Closed") {
			if (this.frm.doc.docstatus == 0) {
				this.frm.add_custom_button(__('Purchase Order'),
					function () {
						if (!me.frm.doc.supplier) {
							frappe.throw({
								title: __("Mandatory"),
								message: __("Please Select a Supplier")
							});
						}
						erpnext.utils.map_current_doc({
							method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
							source_doctype: "Purchase Order",
							target: me.frm,
							setters: {
								supplier: me.frm.doc.supplier,
								schedule_date: undefined
							},
							get_query_filters: {
								docstatus: 1,
								status: ["not in", ["Closed", "On Hold"]],
								per_received: ["<", 99.99],
								company: me.frm.doc.company
							}
						})
					}, __("Get Items From"));
			}

			if(this.frm.doc.docstatus == 1 && this.frm.doc.status!="Closed") {
				if (this.frm.has_perm("submit")) {
					cur_frm.add_custom_button(__("Close"), this.close_purchase_receipt, __("Status"))
				}

				cur_frm.add_custom_button(__('Purchase Return'), this.make_purchase_return, __('Create'));

				cur_frm.add_custom_button(__('Make Stock Entry'), cur_frm.cscript['Make Stock Entry'], __('Create'));

				if(flt(this.frm.doc.per_billed) < 100) {
					cur_frm.add_custom_button(__('Purchase Invoice'), this.make_purchase_invoice, __('Create'));
				}
				// cur_frm.add_custom_button(__('Retention Stock Entry'), this.make_retention_stock_entry, __('Create'));

				// if(!this.frm.doc.auto_repeat) {
				// 	cur_frm.add_custom_button(__('Subscription'), function() {
				// 		erpnext.utils.make_subscription(me.frm.doc.doctype, me.frm.doc.name)
				// 	}, __('Create'))
				// }
				cur_frm.add_custom_button(__('Asset Issue Entry'), this.make_asset_issue_entry, __('Create'));
				cur_frm.page.set_inner_btn_group_as_primary(__('Create'));
			}
		}


		if(this.frm.doc.docstatus==1 && this.frm.doc.status === "Closed" && this.frm.has_perm("submit")) {
			cur_frm.add_custom_button(__('Reopen'), this.reopen_purchase_receipt, __("Status"))
		}

		this.frm.toggle_reqd("supplier_warehouse", this.frm.doc.is_old_subcontracting_flow);
	}

	make_purchase_invoice() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_invoice",
			frm: cur_frm
		})
	}

	make_purchase_return() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_purchase_return",
			frm: cur_frm
		})
	}

	close_purchase_receipt() {
		cur_frm.cscript.update_status("Closed");
	}

	reopen_purchase_receipt() {
		cur_frm.cscript.update_status("Submitted");
	}

	make_retention_stock_entry() {
		frappe.call({
			method: "erpnext.stock.doctype.stock_entry.stock_entry.move_sample_to_retention_warehouse",
			args:{
				"company": cur_frm.doc.company,
				"items": cur_frm.doc.items
			},
			callback: function (r) {
				if (r.message) {
					var doc = frappe.model.sync(r.message)[0];
					frappe.set_route("Form", doc.doctype, doc.name);
				}
				else {
					frappe.msgprint(__("Purchase Receipt doesn't have any Item for which Retain Sample is enabled."));
				}
			}
		});
	}

	make_asset_issue_entry() {
		// console.log("HAHAHA")
		var doc = cur_frm.doc;
		var dialog = new frappe.ui.Dialog({
			title: __("For Issuing Asset"),
			fields: [
				{	"fieldtype": "Select",
					"label": __("Material Name"),
					"fieldname": "item_name",
					"options": doc.items.map(d => d.idx+' '+d.item_name),
					"reqd": 1 
				},
				{	"fieldtype": "Button", "label": __('Issue Asset'),
					"fieldname": "make_asset_issue_entry", "cssClass": "btn-primary"
				},
			]
		});
		
		dialog.fields_dict.make_asset_issue_entry.$input.click(function() {
			var args = dialog.get_values();
			var item = args.item_name;
			var itemIdx = item.substr(0, item.indexOf(" "));
			var itemName = item.substr(item.indexOf(" "), item.length - 1);

			frappe.call({
				method:'frappe.client.get_value',
				args:{
					'doctype':'Item',
					fieldname:"is_fixed_asset",
					filters: {
						"item_name": itemName.trim()
					}
				},
				callback:(r)=>{
					if(r.message){
						if ( !r.message.is_fixed_asset){
							frappe.msgprint('Item selected is not a fixed asset')
							dialog.hide();
							return;
						}
	
						if(!args) return;
						dialog.hide();
	
						let business_activity = ''
						let item_code = ''
						let asset_rate = ''
						let item_desc = ''
						cur_frm.doc.items.map(d => {
							if (d.idx == itemIdx){
								business_activity = cur_frm.doc.business_activity;
								item_code = d.item_code;
								asset_rate = d.base_rate;
								item_desc = d.description;
							}
	
						})
	
						var new_doc = frappe.model.get_new_doc('Asset Issue Details');
						new_doc.branch = cur_frm.doc.branch;
						new_doc.purchase_date = cur_frm.doc.date;
						new_doc.business_activity = business_activity;
						new_doc.entry_date = new Date().toJSON().slice(0,10).replace(/-/g,'-');
						new_doc.item_code = item_code;
						new_doc.item_description = item_desc;
						new_doc.purchase_receipt = cur_frm.docname;
						new_doc.asset_rate = asset_rate
						new_doc.qty = 1;
						new_doc.amount = asset_rate * new_doc.qty
						frappe.set_route('Form', 'Asset Issue Details', new_doc.name);
					} else{
						frappe.msgprint('There no such item')
						dialog.hide();
						return;
					}
				}
			})
		});
		dialog.show()
	}

	apply_putaway_rule() {
		if (this.frm.doc.apply_putaway_rule) erpnext.apply_putaway_rule(this.frm);
	}


};

// for backward compatibility: combine new and previous states
extend_cscript(cur_frm.cscript, new erpnext.stock.PurchaseReceiptController({frm: cur_frm}));

cur_frm.cscript.update_status = function(status) {
	frappe.ui.form.is_saving = true;
	frappe.call({
		method:"erpnext.stock.doctype.purchase_receipt.purchase_receipt.update_purchase_receipt_status",
		args: {docname: cur_frm.doc.name, status: status},
		callback: function(r){
			if(!r.exc)
				cur_frm.reload_doc();
		},
		always: function(){
			frappe.ui.form.is_saving = false;
		}
	})
}

cur_frm.fields_dict['items'].grid.get_field('project').get_query = function(doc, cdt, cdn) {
	return {
		filters: [
			['Project', 'status', 'not in', 'Completed, Cancelled']
		]
	}
}

cur_frm.fields_dict['select_print_heading'].get_query = function(doc, cdt, cdn) {
	return {
		filters: [
			['Print Heading', 'docstatus', '!=', '2']
		]
	}
}

cur_frm.fields_dict['items'].grid.get_field('bom').get_query = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn]
	return {
		filters: [
			['BOM', 'item', '=', d.item_code],
			['BOM', 'is_active', '=', '1'],
			['BOM', 'docstatus', '=', '1']
		]
	}
}

frappe.provide("erpnext.buying");

frappe.ui.form.on("Purchase Receipt", "is_subcontracted", function(frm) {
	if (frm.doc.is_old_subcontracting_flow) {
		erpnext.buying.get_default_bom(frm);
	}

	frm.toggle_reqd("supplier_warehouse", frm.doc.is_old_subcontracting_flow);
});

frappe.ui.form.on('Purchase Receipt Item', {
	item_code: function(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.db.get_value('Item', {name: d.item_code}, 'sample_quantity', (r) => {
			frappe.model.set_value(cdt, cdn, "sample_quantity", r.sample_quantity);
			validate_sample_quantity(frm, cdt, cdn);
		});
	},
	qty: function(frm, cdt, cdn) {
		validate_sample_quantity(frm, cdt, cdn);
	},
	sample_quantity: function(frm, cdt, cdn) {
		validate_sample_quantity(frm, cdt, cdn);
	},
	batch_no: function(frm, cdt, cdn) {
		validate_sample_quantity(frm, cdt, cdn);
	},
});

cur_frm.cscript['Make Stock Entry'] = function() {
	frappe.model.open_mapped_doc({
		method: "erpnext.stock.doctype.purchase_receipt.purchase_receipt.make_stock_entry",
		frm: cur_frm,
	})
}

var validate_sample_quantity = function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	if (d.sample_quantity && d.qty) {
		frappe.call({
			method: 'erpnext.stock.doctype.stock_entry.stock_entry.validate_sample_quantity',
			args: {
				batch_no: d.batch_no,
				item_code: d.item_code,
				sample_quantity: d.sample_quantity,
				qty: d.qty
			},
			callback: (r) => {
				frappe.model.set_value(cdt, cdn, "sample_quantity", r.message);
			}
		});
	}
};
