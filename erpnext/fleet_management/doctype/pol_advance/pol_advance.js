// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('POL Advance', {
	onload: (frm)=>{
		set_party_type(frm);
		frm.set_query("party", function() {
			return {
				"filters": {
					"is_pol_supplier": 1
				}
			};
		});

		frm.set_query("select_cheque_lot", function(){
			return 	{
				"filters":[
					["status", "!=", "Used"],
					["docstatus", "=", "1"],
				]
			}
		});

	},
	equipment:function(frm){
		frm.events.set_fuelbook_filter(frm)
		frm.events.set_advance_limit(frm)
	},
	use_common_fuelbook:function(frm){
		frm.events.set_fuelbook_filter(frm)
	},
	set_fuelbook_filter:function(frm){
		if (frm.doc.use_common_fuelbook){
			frm.set_query("fuel_book",function(){
				return {
					filters:{
						"type":"Common"
					}
				}
			})
		}else{
			frm.set_query("fuel_book",function(){
				return {
					filters:{
						"equipment":frm.doc.equipment
					}
				}
			})
		}
	},
	fuel_book: function(frm){
		frm.events.set_advance_limit(frm)
	},
	set_advance_limit: function(frm){
		if (frm.doc.equipment || frm.doc.fuel_book){
			frappe.call({
				method: "set_advance_limit",
				doc: frm.doc,

				callback: function(r) {
					frm.refresh_field("advance_limit");
					frm.dirty()
				}
			});
		}
	},
	refresh: function(frm){
		enable_disable(frm);
		open_ledger(frm);
	},
	party_type: (frm)=>{
		set_party_type(frm);
	},
	amount:(frm)=>{
		calculate_balance(frm);
	},
	use_cheque_lot: function(frm){
		enable_disable(frm);
	},

	select_cheque_lot: function (frm) {
		if (frm.doc.select_cheque_lot) {
			frappe.call({
				method: "erpnext.accounts.doctype.cheque_lot.cheque_lot.get_cheque_no_and_date",
				args: {
					'name': frm.doc.select_cheque_lot
				},
				callback: function (r) {
					if (r.message) {
						cur_frm.set_value("cheque_no", r.message[0].reference_no);
						cur_frm.set_value("cheque_date", r.message[1].reference_date);
					}
				}
			});
		}
	},
	cheque_no: function(frm){
		enable_disable(frm);
	},
	cheque_date: function(frm){
		enable_disable(frm);
	}
});
function enable_disable(frm) {
	if(frm.doc.use_cheque_lot){
		frm.toggle_reqd(['cheque_no','cheque_date'], frm.doc.use_cheque_lot);
	} else {
		frm.toggle_reqd(['cheque_date'], frm.doc.cheque_no);
		frm.toggle_reqd(['cheque_no'], frm.doc.cheque_date);
	}
}

var calculate_balance=(frm)=>{
	if (frm.doc.amount > 0 ){
		cur_frm.set_value("balance_amount",frm.doc.amount)
		cur_frm.set_value("adjusted_amount",0)
	}
}
var open_ledger = (frm)=>{
	if (frm.doc.docstatus === 1  && frm.doc.is_opening == 0) {
		frm.add_custom_button(
		  __("Journal Entry"),
		  function () {
			frappe.route_options = {
			  name: frm.doc.journal_entry,
			  from_date: frm.doc.entry_date,
			  to_date: frm.doc.entry_date,
			  company: frm.doc.company,
			};
			frappe.set_route("List", "Journal Entry");
		  },
		  __("View")
		);
	}
 }
var set_party_type = (frm)=>{
	cur_frm.set_query('paty_type', (frm)=> {
		return {
			'filters': {
				'name': 'Supplier'
			}
		};
	});
}
