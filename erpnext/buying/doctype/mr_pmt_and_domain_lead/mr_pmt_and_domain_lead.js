// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('MR PMT And Domain Lead', {
	// refresh: function(frm) {

	// }
	setup: function(frm){
		frm.set_query("cost_center", "domain_item", function() {
			return {
				filters: {
					center_category: "Course",
					cost_center_for: "DSP",
					is_group: 0
				}
			};
		});
		frm.set_query("cost_center", "pmt_item", function() {
			return {
				filters: {
					center_category: "Course",
					cost_center_for: "DSP",
					is_group: 0
				}
			};
		});
	},
	get_cc_list: function(frm){
		frm.trigger("get_domain_list");
	},
	get_domain_list: function(frm){
		var dialog = new frappe.ui.Dialog({
			title: __("Get Cost Center List from Domain"),
			fields: [
				{"fieldtype": "Link", "label": __("Cost Center"),
					"fieldname": "cost_center", "options":"Cost Center",
					"reqd": 1,
					"get_query": function () {
					    return {
					        filters: [
					            ["Cost Center", "disabled", "=", 0],
					            ["Cost Center", "is_group", "=", 1],
					            ["Cost Center", "center_category", "=", "Domain"],
					            ["Cost Center", "cost_center_for", "=", "DSP"]
					        ]
					    };
					},
				},
			]
		});
		
		dialog.set_primary_action(__('Get List'), function(frm) {
			dialog.hide();
			var args = dialog.get_values();
			// console.log(args)
			frappe.call({
				method: "get_domain_list",
				doc: cur_frm.doc,
				args: {
					"cost_center": args.cost_center             
				},
				callback: function (r) {
					console.log(r.message)
					cur_frm.refresh_field("domain_item");
					// frm.refresh_fields();
					// cur_frm.reload_doc();
				}
			});
		});
		
		dialog.show()
	},
	get_cc_pmt_list: function(frm){
		frm.trigger("get_pmt_list");
	},
	get_pmt_list: function(frm){
		var dialog = new frappe.ui.Dialog({
			title: __("Get Cost Center List from Domain"),
			fields: [
				{"fieldtype": "Link", "label": __("Cost Center"),
					"fieldname": "cost_center", "options":"Cost Center",
					"reqd": 1,
					"get_query": function () {
					    return {
					        filters: [
					            ["Cost Center", "disabled", "=", 0],
					            ["Cost Center", "is_group", "=", 1],
					            ["Cost Center", "center_category", "=", "Domain"],
					            ["Cost Center", "cost_center_for", "=", "DSP"]
					        ]
					    };
					},
				},
			]
		});
		
		dialog.set_primary_action(__('Get List'), function(frm) {
			dialog.hide();
			var args = dialog.get_values();
			// console.log(args)
			frappe.call({
				method: "get_pmt_list",
				doc: cur_frm.doc,
				args: {
					"cost_center": args.cost_center             
				},
				callback: function (r) {
					console.log(r.message)
					cur_frm.refresh_field("pmt_item");
				}
			});
		});
		
		dialog.show()
	}
});