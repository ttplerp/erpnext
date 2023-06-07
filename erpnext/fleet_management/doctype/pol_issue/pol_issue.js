// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('POL Issue', {
	refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
			frm.add_custom_button(
				__("Ledger"),
				function () {
				  frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false,
				  };
				  frappe.set_route("query-report", "General Ledger");
				},
				__("View")
			  );
		}
		if(frm.doc.docstatus == 1 && cint(frm.doc.out_source) == 0) {
			cur_frm.add_custom_button(__('POL Ledger'), function() {
				frappe.route_options = {
					branch: frm.doc.branch,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					equipment: frm.doc.tanker
				};
				frappe.set_route("query-report", "POL Ledger");
			}, __("View"));
		}
		set_equipment_filter(frm)
	},
	branch:function(frm){
		set_equipment_filter(frm)
	},
});

cur_frm.set_query("pol_type", function() {
	return {
		"filters": {
		"disabled": 0,
		"is_pol_item":1
		}
	};
});

var set_equipment_filter=function(frm){
	frm.set_query("tanker", function() {
		return {
			query: "erpnext.fleet_management.fleet_utils.get_container_filtered",
			filters:{}
		};
	});
	frm.set_query('equipment', 'items', function (doc, cdt, cdn) {
		return {
			filters: {
				"enabled": 1,
				"is_container":0
			}
		}
	});
}

frappe.ui.form.on('POL Issue Items', {
	"equipment":function(frm, cdt, cdn){
		let row = locals[cdt][cdn]
		frm.set_query('fuelbook', 'items', function (doc, cdt, cdn) {
			return {
				filters: {
					"equipment": row.equipment
				}
			}
		});
	}
})