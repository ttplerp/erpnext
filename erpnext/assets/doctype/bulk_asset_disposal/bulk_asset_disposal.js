// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Asset Disposal', {
	onload: function (frm) {
		frm.set_query("asset", "item", (doc) => {
			return {
				filters: {
					asset_category:doc.asset_category,
					// status: ["not in", ["Draft","Sold","Scrapped","Submitted","Cancelled"]],
					status: ["in", ["Fully Depreciated"]],
				}
			}
		})
	},
	refresh: function (frm) {
		if ((frm.doc.docstatus == 1 && frm.doc.scrap == "Sale Asset") && frm.doc.sales_invoice == null) {
			cur_frm.add_custom_button(__("Make Sales Invoice"),
				function () {
					frm.events.make_sales_invoice(frm);
				}
			).addClass("btn-primary custom-create custom-create-css")
		}
	},
	scrap: function (frm) {
		// frm.doc.scrap_date = Date.now(); #comment by Jai, 20 July 2022
		// frm.refresh_fields()
		frm.set_df_property('customer', 'reqd', frm.doc.scrap=='Sale Asset'? 1:0)
	},
	make_sales_invoice: function (frm) {
		frappe.call({
			method: "erpnext.assets.doctype.bulk_asset_disposal.bulk_asset_disposal.sale_asset",
			args: {
				branch: frm.doc.branch,
				// business_activity: frm.doc.business_activity,
				name: frm.doc.name,
				scrap_date: frm.doc.scrap_date,
				customer: frm.doc.customer,
				posting_date: frm.doc.scrap_date
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			}
		});
	},
	
	// asset_category:function(frm){
	// 	console.log(frm.doc.asset_category)
	// 	cur_frm.fields_dict['item'].grid.get_field('asset').get_query = function(doc, cdt, cdn) {
	// 		return {
	// 			filters:{
	// 				"asset_category":doc.asset_category,
	// 				"status":['in',['Submitted','Fully Depreciated','Partially Depreciated']]
	// 			}
	// 		}
	// 	}
	// },
	// added by Jai, 9/12/2021
	on_submit: function(frm) {
		console.log("on_submit")
		if(frm.doc.scrap == 'Scrap Asset'){
			frappe.set_route("List", "Journal Entry");
		}
	}
});


frappe.ui.form.on('Bulk Asset Disposal Item', {
	// asset:function(frm,cdt,cdn){

	// }
	item_code:function(frm,cdt,cdn){
		var item = locals[cdt][cdn]
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Item",
				fieldname: ["item_name", "stock_uom"],
				filters: {
					name: item.item_code
				}
			},
			callback: function(r) {
				frappe.model.set_value(cdt, cdn, "item_name", r.message.item_name)
				frappe.model.set_value(cdt, cdn, "uom", r.message.stock_uom)
				cur_frm.refresh_field("item_name")
				cur_frm.refresh_field("uom")
			}
		})
	}
})
frappe.form.link_formatters['Item'] = function(value, doc) {
	return value
}
