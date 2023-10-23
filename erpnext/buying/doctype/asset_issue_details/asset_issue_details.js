// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Asset Issue Details', {
	onload: function(frm){
		frm.set_query('branch', function(doc, cdt, cdn) {
			return {
				filters: {
					"disabled": 0
				}
			};
		});

		frm.set_query('receiving_branch', function(doc, cdt, cdn) {
			return {
				filters: {
					"disabled": 0
				}
			};
		});
	},

	// item_code: function(frm) {
	// 	me.frm.set_query("purchase_receipt",function(doc) {
	// 		return {
	// 			query: "erpnext.buying.doctype.asset_issue_details.asset_issue_details.check_item_code",
	// 			filters: {
	// 				'item_code': doc.item_code,
	// 			}
	// 		}
	// 	});
	// },
	refresh: function (frm) {

	},
	"qty": function (frm) {
		if (frm.doc.asset_rate) {
			frm.set_value("amount", frm.doc.qty * frm.doc.asset_rate);
		}
	},
	"asset_rate": function (frm) {
		if (frm.doc.qty) {
			frm.set_value("amount", frm.doc.qty * frm.doc.asset_rate);
		}
	},
	// "purchase_receipt": function(frm){
	// 	frappe.call({
	// 		method: "frappe.client.get_value",
	// 		args: {
	// 			parent: "Purchase Receipt",
	// 			doctype: "Purchase Receipt Item",
	// 			fieldname: ["base_rate", "description"],
	// 			filters: {
	// 				"parent": frm.doc.purchase_receipt,
	// 				"item_code": frm.doc.item_code,
	// 				"description": (frm.doc.item_description != "")? frm.doc.item_description : ""
	// 			}
	// 		},
	// 		callback: function(r){
	// 			if(r.message.base_rate){
	// 				cur_frm.set_value("asset_rate", r.message.base_rate)
	// 				cur_frm.set_value("item_description", r.message.description)
	// 			}
	// 			else{
	// 				frappe.throw("Not working")
	// 			}
	// 		}
	// 	});
	// }
});

cur_frm.fields_dict['item_code'].get_query = function (doc) {
	return {
		"filters": {
			"item_group": "Fixed Asset"
		}
	}
}