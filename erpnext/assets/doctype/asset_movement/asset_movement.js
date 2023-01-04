// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Asset Movement', {
	refresh: function(frm) {
		if(frm.doc.docstatus == 1) {
			cur_frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: moment(frm.doc.transaction_date).format("YYYY-MM-DD"),
					to_date: moment(frm.doc.transaction_date).format("YYYY-MM-DD"),
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}
	},
	setup: (frm) => {
		frm.set_query("to_employee", "assets", (doc) => {
			return {
				filters: {
					company: doc.company
				}
			};
		})
		frm.set_query("from_employee", "assets", (doc) => {
			return {
				filters: {
					company: doc.company
				}
			};
		})
		frm.set_query("reference_name", (doc) => {
			return {
				filters: {
					company: doc.company,
					docstatus: 1
				}
			};
		})
		frm.set_query("reference_doctype", () => {
			return {
				filters: {
					name: ["in", ["Purchase Receipt", "Purchase Invoice"]]
				}
			};
		}),
		frm.set_query("asset", "assets", () => {
			return {
				filters: {
					status: ["not in", ["Draft","Scrapped"]]
				}
			}
		})
	},

	onload: (frm) => {
		// frm.trigger('set_required_fields');
	},

	purpose: (frm) => {
		// frm.trigger('set_required_fields');
	},

	set_required_fields: (frm, cdt, cdn) => {
		let fieldnames_to_be_altered;
		if (frm.doc.purpose === 'Transfer') {
			fieldnames_to_be_altered = {
				target_location: { read_only: 0, reqd: 1 },
				source_location: { read_only: 1, reqd: 1 },
				from_employee: { read_only: 1, reqd: 0 },
				to_employee: { read_only: 1, reqd: 0 }
			};
		}
		else if (frm.doc.purpose === 'Receipt') {
			fieldnames_to_be_altered = {
				target_location: { read_only: 0, reqd: 1 },
				source_location: { read_only: 1, reqd: 0 },
				from_employee: { read_only: 0, reqd: 1 },
				to_employee: { read_only: 1, reqd: 0 }
			};
		}
		else if (frm.doc.purpose === 'Issue') {
			fieldnames_to_be_altered = {
				target_location: { read_only: 1, reqd: 0 },
				source_location: { read_only: 1, reqd: 1 },
				from_employee: { read_only: 1, reqd: 0 },
				to_employee: { read_only: 0, reqd: 1 }
			};
		}
		Object.keys(fieldnames_to_be_altered).forEach(fieldname => {
			let property_to_be_altered = fieldnames_to_be_altered[fieldname];
			Object.keys(property_to_be_altered).forEach(property => {
				let value = property_to_be_altered[property];
				frm.set_df_property(fieldname, property, value, cdn, 'assets');
			});
		});
		frm.refresh_field('assets');
	},
	get_asset: function(frm){
		get_asset_list(frm);
	}
});

function get_asset_list(frm){
	frappe.call({
		method:"get_asset_list",
		doc: frm.doc,
		callback: function (){
			frm.refresh_field("assets");
		}
	});
	
}

frappe.ui.form.on('Asset Movement Item', {
	asset: function(frm, cdt, cdn) {
		// on manual entry of an asset auto sets their source cost center / employee
		const asset_name = locals[cdt][cdn].asset;
		if (asset_name){
			frappe.db.get_doc('Asset', asset_name).then((asset_doc) => {
				if(asset_doc.cost_center ) frappe.model.set_value(cdt, cdn, 'source_cost_center', asset_doc.cost_center);
				if(asset_doc.issued_to){
					frappe.model.set_value(cdt, cdn, 'source_custodian_type',  asset_doc.issued_to ?? '');
					frappe.model.set_value(cdt, cdn, 'from_employee',  (asset_doc.issued_to == 'Employee') ? asset_doc.issue_to_employee : '');
					frappe.model.set_value(cdt, cdn, 'from_employee_name',  (asset_doc.issued_to == 'Employee') ? asset_doc.employee_name : '');
					frappe.model.set_value(cdt, cdn, 'from_desuup',  (asset_doc.issued_to == 'Desuup') ? asset_doc.issue_to_desuup : '');
					frappe.model.set_value(cdt, cdn, 'from_desuup_name',  (asset_doc.issued_to == 'Desuup') ? asset_doc.desuup_name : '');
					frappe.model.set_value(cdt, cdn, 'others',  (asset_doc.issued_to == 'Other') ? asset_doc.issue_to_other : '');
				} 
				// frm.refresh_field('assets')
			}).catch((err) => {
			});
		}
	},
	target_custodian_type: function(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, 'to_employee', '');
		frappe.model.set_value(cdt, cdn, 'to_employee_name', '');
		frappe.model.set_value(cdt, cdn, 'to_desuup', '');
		frappe.model.set_value(cdt, cdn, 'to_desuup_name', '');
		frappe.model.set_value(cdt, cdn, 'to_other', '');
		frappe.model.set_value(cdt, cdn, 'target_cost_center', '');
		frm.refresh_field('assets');
	},
	to_employee: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.target_custodian_type == 'Employee') {
			cur_frm.add_fetch('to_employee','cost_center','target_cost_center');
		}
	}
});
