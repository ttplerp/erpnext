// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Asset Movement', {
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
					status: ["not in", ["Draft"]]
				}
			}
		})
	},

	onload: (frm) => {
		frm.trigger('set_required_fields');
	},

	purpose: (frm) => {
		frm.trigger('set_required_fields');
	},
	transfer_type: (frm) => {
		var me = this;
		me.frm.doc.assets.forEach((item)=>{
			var asset_custodian = ''
			var asset_cost_center = ''
			me.frm.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Asset",
					filters: {"name": item.asset},
					fieldname: "cost_center",
				},
				async: false,
				callback: function(r){
					asset_cost_center = r.message.cost_center;
				}
			})
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Asset",
					filters: {"name": item.asset},
					fieldname: "custodian",
				},
				async: false,
				callback: function(r){
					asset_custodian = r.message.custodian;
				}
			})
			if(frm.doc.transfer_type == "Cost Center To Cost Center"){
				frappe.model.set_value(item.doctype, item.name, 'from_employee', null);
				frappe.model.set_value(item.doctype, item.name, 'source_cost_center', asset_cost_center);
			}
			else if(frm.doc.transfer_type == "Employee To Employee"){
				if(asset_custodian == null || asset_custodian == undefined || asset_custodian == ''){
					frappe.throw("No Asset Custodian for Asset <a href='/app/asset/"+String(item.asset)+"'>"+String(item.asset)+"</a>")
				}
				frappe.model.set_value(item.doctype, item.name, 'source_cost_center', null);
				frappe.model.set_value(item.doctype, item.name, 'from_employee', asset_custodian);

			}
		})
		frm.refresh_field("assets");
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
	}
});

frappe.ui.form.on('Asset Movement Item', {
	asset: function(frm, cdt, cdn) {
		// on manual entry of an asset auto sets their source cost center / employee
		const asset_name = locals[cdt][cdn].asset;
		if (asset_name){
			frappe.db.get_doc('Asset', asset_name).then((asset_doc) => {
				if(asset_doc.cost_center ) frappe.model.set_value(cdt, cdn, 'source_cost_center', asset_doc.cost_center);
				if(asset_doc.custodian) frappe.model.set_value(cdt, cdn, 'from_employee', asset_doc.custodian);
				// frm.refresh_field('assets')
			}).catch((err) => {
			});
		}
	}
});
