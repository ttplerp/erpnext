// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('POL Receive', {
	refresh: function(frm) {
		refresh_html(frm);
		// if (frm.doc.docstatus === 1 ) {
		// 	frm.add_custom_button(__("Ledger"), function () {
		// 		frappe.route_options = {
		// 			voucher_no: frm.doc.name,
		// 			from_date: frm.doc.entry_date,
		// 			to_date: frm.doc.entry_date,
		// 			company: frm.doc.company,
		// 			group_by_voucher: false,
		// 		};
		// 		frappe.set_route("query-report", "General Ledger");
		// 	}, __("View"));
		// }
		if(!frm.doc.__islocal){
			// if(frappe.model.can_read("Project")) {
				if(frm.doc.journal_entry){
					frm.add_custom_button(__('Journal Entry'), function() {
							frappe.route_options = {"name": frm.doc.journal_entry};
							frappe.set_route("List", "Journal Entry");
					}, __("View"));
				}
			// }
		}
		if(frm.doc.docstatus==1 && frm.doc.receive_in_barrel ==1) {
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

		// if (frm.doc.docstatus == 1 && frm.doc.settle_imprest_advance != 1) {
		// 	cur_frm.add_custom_button(__('POL Receive Invoice'), function(doc) {
		// 		frm.events.make_pol_receive_invoice(frm)
		// 	},__("Create"))
		// 	frm.page.set_inner_btn_group_as_primary(__('Create'));
		// }
	},
	qty: function(frm) {
		calculate_total(frm)
		frm.events.reset_items()
		frm.refresh_fields("items")
	},
	direct_consumption:function(frm){
		set_equipment_filter(frm)
	},
	rate: function(frm) {
		frm.events.reset_items()
		frm.refresh_fields("items")
		calculate_total(frm)
	},
	get_pol_expense:function(frm){
		populate_child_table(frm)
	},
	settle_imprest_advance: function(frm){
		if(frm.doc.settle_imprest_advance==0 || frm.doc.settle_imprest_advance == undefined){
			frm.set_value("party",null);
			frm.refresh_field("party");
		}
	},
	branch:function(frm){
		// frm.set_query("equipment",function(){
		// 	return {
		// 		filters:{
		// 			"branch":frm.doc.branch,
		// 			"enabled":1
		// 		}
		// 	}
		// })
	},
	equipment:function(frm){
		frm.set_query("fuelbook",function(){
			return {
				filters:{
					"equipment":frm.doc.equipment
				}
			}
		})
		get_previous_km_reading(frm);
	},
	reset_items:function(frm){
		cur_frm.clear_table("items");
	},

	make_pol_receive_invoice: function(frm) {
		frappe.call({
			method: "make_pol_receive_invoice",
			doc:frm.doc,
			callback:function(r){
                cur_frm.reload_doc()
            },
			// freeze: true,
			// freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Posting To account.....</span>'
		})
	}
});
cur_frm.set_query("pol_type", function() {
	return {
		"filters": {
		"disabled": 0,
		"is_pol_item":1
		}
	};
});
var populate_child_table=(frm)=>{
	if (frm.doc.fuelbook && frm.doc.total_amount) {
		frappe.call({
			method: 'populate_child_table',
			doc: frm.doc,
			callback:  () =>{
				cur_frm.refresh_fields()
				frm.dirty()
			}
		})
	}
}
function calculate_total(frm) {
	if(frm.doc.qty && frm.doc.rate) {
		frm.set_value("total_amount", frm.doc.qty * frm.doc.rate)
	}

	if(frm.doc.qty && frm.doc.rate && frm.doc.discount_amount) {
		frm.set_value("total_amount", (frm.doc.qty * frm.doc.rate) - frm.doc.discount_amount)
	}
}	

var set_equipment_filter=function(frm){
	if ( cint(frm.doc.direct_consumption) == 0){
		frm.set_query("equipment", function() {
			return {
				query: "erpnext.fleet_management.fleet_utils.get_container_filtered",
				filters:{
					"branch":frm.doc.branch
				}
			};
		});
	}
}

var get_previous_km_reading = (frm) => {
	frappe.call({
		method: "get_previous_km_reading",
		doc: frm.doc,
		callback: function (r) {
			frm.set_value("previous_km", r.message);
			frm.refresh_field("previous_km");
		}
	})
}

var refresh_html = function(frm){
	var journal_entry_status = "";
	if(frm.doc.journal_entry_status){
		journal_entry_status = '<div style="font-style: italic; font-size: 0.8em; ">* '+frm.doc.journal_entry_status+'</div>';
	}
	
	if(frm.doc.journal_entry){
		$(cur_frm.fields_dict.journal_entry_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Journal Entry</label><br><b>'+'<a href="/desk#Form/Journal Entry/'+frm.doc.journal_entry+'">'+frm.doc.journal_entry+"</a> "+"</b>"+journal_entry_status);
	}	
}