// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("branch", "cost_center", "cost_center")
cur_frm.add_fetch("item_code", "item_name", "item_name")
cur_frm.add_fetch("item_code", "stock_uom", "uom")
cur_frm.add_fetch("item_code", "item_group", "item_group")
cur_frm.add_fetch("equipment", "equipment_model", "equipment_model");
cur_frm.add_fetch("equipment", "equipment_number", "equipment_number");
cur_frm.add_fetch("location", "distance", "distance");

frappe.ui.form.on('Production', {
	onload: function(frm) {
		if (!frm.doc.posting_date) {
				frm.set_value("posting_date", get_today());
		}
	},
	setup: function(frm) {
		frm.get_docfield("raw_materials").allow_bulk_edit = 1;	
		frm.get_docfield("items").allow_bulk_edit = 1;
		frm.get_field('raw_materials').grid.editable_fields = [
			{fieldname: 'item_code', columns: 3},
			{fieldname: 'item_type', columns: 3},
			{fieldname: 'qty', columns: 2},
			{fieldname: 'uom', columns: 1},
		];
		frm.get_field('items').grid.editable_fields = [
			{fieldname: 'item_code', columns: 3},
			{fieldname: 'qty', columns: 2},
			{fieldname: 'uom', columns: 1},
			{fieldname: 'item_type', columns: 2},
			{fieldname: 'equipment_number', columns: 2},
		];
	},
	
	refresh: function(frm) {
		if(frm.doc.docstatus == 1) {
			// cur_frm.add_custom_button(__("Stock Ledger"), function() {
			// 	frappe.route_options = {
			// 		voucher_no: frm.doc.name,
			// 		from_date: frm.doc.posting_date,
			// 		to_date: frm.doc.posting_date,
			// 		company: frm.doc.company
			// 	};
			// 	frappe.set_route("query-report", "Stock Ledger Report");
			// }, __("View"));

			cur_frm.add_custom_button(__('Accounting Ledger'), function() {
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
		apply_filter(frm)
	},
	branch: function(frm){
		frm.set_value("warehouse","");
	//Added by Birendra on 10/05/2021
		apply_filter(frm)
	},
	warehouse: function(frm){
		update_items(frm);
	},
	cost_center: function(frm){
		update_items(frm);
	},
	get_product: function(frm){
		get_finish_product(frm);
	},
	get_raw_material: function(frm){
		get_raw_materials(frm);
	},
	//Added by Birendra on 10/05/2021
	coal_raising_type:function(frm){
		make_field_mandatory(frm)
		apply_filter(frm)
	}
});

frappe.ui.form.on("Production", "refresh", function(frm) {
    cur_frm.set_query("warehouse", function() {
        return {
            query: "erpnext.controllers.queries.filter_branch_wh",
            filters: {'branch': frm.doc.branch}
        }
    });

    cur_frm.set_query("branch", function() {
        return {
            "filters": {
			"disabled": 0
            }
        };
    });

    cur_frm.set_query("location", function() {
        return {
            "filters": {
                "branch": frm.doc.branch,
		"is_disabled": 0
            }
        };
    });
})

frappe.ui.form.on("Production Product Item", {
	"refresh": function(frm, cdt, cdn) {
	}, 
	"price_template": function(frm, cdt, cdn) {
		d = locals[cdt][cdn]
		frappe.call({
			method: "erpnext.production.doctype.cop_rate.cop_rate.get_cop_amount",
			args: {
				"item_code": d.item_code,
				"posting_date": cur_frm.doc.posting_date 
			},
			callback: function(r) {
				frappe.model.set_value(cdt, cdn, "rate", r.message)
				cur_frm.refresh_field("rate")
			}
		})
	},
	transporter_payment_eligible: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if(row.transporter_payment_eligible){
			cur_frm.get_field("items").grid.toggle_reqd("equipment", true);
		}else{
			cur_frm.get_field("items").grid.toggle_reqd("equipment", false);
		}
	},

	item_code: function(frm, cdt, cdn) {
		/* ++++++++++ Ver 1.0.190401 Begins ++++++++++*/
		// Following code added by SHIV on 2019/04/01
		update_expense_account(frm, cdt, cdn);
		/* ++++++++++ Ver 1.0.190401 Ends ++++++++++++*/
		frappe.model.set_value(cdt, cdn, "production_type", frm.doc.production_type);
		cur_frm.refresh_fields();
		// added by Birendra for coal raising purpose on 20/05/2021
		check_item_applicable_for_coal_raising(frm,cdt,cdn)
	},
	
	items_add: function(frm, cdt, cdn){
		frappe.model.set_value(cdt, cdn, "warehouse", frm.doc.warehouse);
		frappe.model.set_value(cdt, cdn, "cost_center", frm.doc.cost_center);
	}
});

function get_finish_product(frm){
	if (frm.doc.branch && frm.doc.raw_materials){
		return frappe.call({
				method: "get_finish_product",
				doc: cur_frm.doc,
				callback: function(r, rt){					
					if(r.message){
						console.log(r.message);
						cur_frm.clear_table("items");
						cur_frm.clear_table("production_waste");
						r.message.forEach(function(rec) {
							if(rec['parameter_type'] == "Item")
							{	
								var row = frappe.model.add_child(cur_frm.doc, "Production Product Item", "items");
								row.item_code = rec['item_code'];
								row.item_name = rec['item_name'];
								row.item_type = rec['item_type'];		
								row.qty = rec['qty'];
								row.uom = rec['uom'];
								row.item_group = rec['item_group'];
								row.price_template = rec['price_template'];
								row.cop = rec['cop'];
								row.cost_center = rec['cost_center'];
								row.warehouse = rec['warehouse'];
								row.expense_account = rec['expense_account'];
								row.ratio = rec['ratio'];
							}
							else{
								var row = frappe.model.add_child(cur_frm.doc, "Production Waste", "production_waste");
								row.parameter_code = rec['item_code'];
								row.item_name = rec['item_name'];
								row.ratio = rec['ratio'];		
								row.qty = rec['qty'];
								row.uom = rec['uom'];
							}
						});
					}
					else
					{
						cur_frm.clear_table("items");
					}					
				cur_frm.refresh();
				},
            });     
	}else{
		frappe.msgprint("To get the finish product, please enter the branch and raw material");
	}
}

function get_raw_materials(frm){
	if (frm.doc.branch && frm.doc.items){
		return frappe.call({
				method: "get_raw_material",
				doc: cur_frm.doc,
				callback: function(r, rt){					
					if(r.message){
						console.log(r.message);
						cur_frm.clear_table("raw_materials");
						r.message.forEach(function(rec) {
							if(rec['parameter_type'] == "Item")
							{	
								var row = frappe.model.add_child(cur_frm.doc, "Production Material Item", "raw_materials");
								row.item_code = rec['item_code'];
								row.item_name = rec['item_name'];	
								row.item_type = rec['item_type'];	
								row.qty = rec['qty'];
								row.uom = rec['uom'];
								row.cost_center = rec['cost_center'];
								row.warehouse = rec['warehouse'];
								row.expense_account = rec['expense_account'];
							}
						});
					}
					else
					{
						cur_frm.clear_table("raw_materials");
					}					
				cur_frm.refresh();
				},
            });     
	}else{
		frappe.msgprint("To get the Raw Materials, please enter the branch and finish product in Production Setting");
	}
}

var update_items = function(frm){
	// Production Product Item
	var items = frm.doc.items || [];
	for(var i=0; i<items.length; i++){
		frappe.model.set_value("Production Product Item", items[i].name, "cost_center", frm.doc.cost_center);
		frappe.model.set_value("Production Product Item", items[i].name, "warehouse", frm.doc.warehouse);
	}
	// Production Material Item
	var raw_materials = frm.doc.raw_materials || [];
	for(var i=0; i<raw_materials.length; i++){
		frappe.model.set_value("Production Material Item", raw_materials[i].name, "cost_center", frm.doc.cost_center);
		frappe.model.set_value("Production Material Item", raw_materials[i].name, "warehouse", frm.doc.warehouse);
	}
}

var make_field_mandatory = (frm)=>{
	if(frm.doc.coal_raising_type == 'Manual' || frm.doc.coal_raising_type == 'Machine Sharing'){
		frm.set_df_property('group', 'reqd', 1)
		frm.set_df_property('no_of_labours', 'reqd', 1)
		if (frm.doc.coal_raising_type == 'Machine Sharing'){
			frm.set_df_property('machine_hours', 'reqd', 1)
		}
	}else{
		frm.set_df_property('group', 'reqd', 0)
		frm.set_df_property('no_of_labours', 'reqd', 0)
		frm.set_df_property('machine_hours', 'reqd', 0)
	}
}

var apply_filter=(frm)=>{
	cur_frm.set_query("group", function() {
		return {
			filters: [
				['branch','=', frm.doc.branch],
				["contract_end_date",'>=',frm.doc.posting_date]
			]
		}
	})
}