// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Revised Technical Sanction', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button("Prepare Bill", function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.rental_management.doctype.revised_technical_sanction.revised_technical_sanction.prepare_bill",
					frm: cur_frm
				});
			});
		}
	},
	setup: function(frm) {
		frm.set_query("service", "items", function(frm,cdt,cdn) {
			var row = locals[cdt][cdn];
			// var is_service_item = (row.type == 'Service')? 1:0;
			if (row.type == undefined || row.type == '') return
			if (row.type == "Service") {
				if(!row.price_list) frappe.throw(__("Please select Price List First"));
				return {
					filters: [
						["disabled", "=", 0],
						["is_service_item", "=", 1],
						// ["is_bsr_service_item", "=", 1]
					]
				}
			} else if (row.type == "Item") {
				return {
					filters: [
						["disabled", "=", 0],
						["is_service_item", "=", 0]
					]
				}
			}
		});
		frm.set_query("price_list", "items", function(frm,cdt,cdn) {
			var row = locals[cdt][cdn];
			console.log(cur_frm.doc.company);
			if (row.type != 'Service') return
			return {
				query: "erpnext.rental_management.doctype.technical_sanction.technical_sanction.get_price_list",
				filters: {
					'company': cur_frm.doc.company,
					'region': cur_frm.doc.region
				}
			};
		});
	}
});

frappe.ui.form.on('Technical Sanction Item', {
	"type": function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.type == 'Service' || row.type == 'Item'){
			frappe.model.set_value(cdt, cdn, "item_type", "Item");
		} else if (row.type == 'Rate Analysis') {
			frappe.model.set_value(cdt, cdn, "item_type", "Rate Analysis");
		} else {
			frappe.model.set_value(cdt, cdn, "item_type", "");
		}
		// refresh_field("detail_measurement");
		frappe.model.set_value(cdt, cdn, "service","");
		// if (row.service){
		// 	frappe.model.set_value(cdt, cdn, "service","");
		// 	frappe.model.set_value(cdt, cdn, "qty", 0);
		// 	frappe.model.set_value(cdt, cdn, "amount", 0.0);
		// 	frappe.model.set_value(cdt, cdn, "total", 0.0);
		// }
		if (row.price_list){
			frappe.model.set_value(cdt, cdn, "price_list","");
		}
	},
	// "price_list": function (frm, cdt, cdn) {
	// 	var row = locals[cdt][cdn];
	// 	return frm.call({
	// 		method: "erpnext.rental_management.doctype.technical_sanction.technical_sanction.get_price_list",
	// 		child: row,
	// 		args: {
	// 			company: frm.doc.company,
	// 			region: frm.doc.region
	// 		}
	// 	});
	// },
	"service": function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		cur_frm.add_fetch("service", "item_name", "item_name");
		cur_frm.add_fetch("service", "stock_uom", "uom");
		
		if (!row.service) return
		// frappe.model.set_value(cdt, cdn, "qty", 0);
		// frappe.model.set_value(cdt, cdn, "amount", 0.0);
		// frappe.model.set_value(cdt, cdn, "total", 0.0);


		if (row.type == 'Service') {
			if(!row.uom) return
			get_item_price(frm, cdt, cdn);
		} else if (row.type == 'Rate Analysis') {
			frappe.model.get_value("Rate Analysis", { 'name': row.service }, ['total_amount'],
				function (d) {
					console.log(d);
					frappe.model.set_value(cdt, cdn, 'amount', d.total_amount);
			});
		} else if (row.type == 'Item') {
			console.log("Item");
		}
		
	},
	"qty": function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "total", row.amount * row.qty);
		var total = 0;
		for (var i in cur_frm.doc.items) {
			var item = cur_frm.doc.items[i];
			total += item.total;
		}
		cur_frm.set_value("total_amount", total);
	}
});

function get_item_price(frm, cdt, cdn)
{
	var row = locals[cdt][cdn];
	frappe.call({
		method: "get_item_price",
		doc: frm.doc,
		args: {
			item_code: row.service,
			price_list: row.price_list,
			uom: row.uom,
			posting_date: frm.doc.posting_date
		},
		callback: function(r) {
			console.log(r.message);
			// if (r.message.length == 0) frappe.throw(__("Missing Item in Price List"));
			frappe.model.set_value(cdt, cdn, "amount", r.message[0][1] ?? 0.0)
		}
	});
}