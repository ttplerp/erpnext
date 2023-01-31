// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pol Advance', {
	onload: function(frm) {
		set_party_type(frm);
		cur_frm.set_query("select_cheque_lot", function(){
			return {
				"filters": [
					["status", "!=", "Used"],
					["docstatus", "=", "1"]
				]
			}
		});
	},
	party_type: (frm)=>{
		set_party_type(frm);
	},
	refresh: (frm)=>{
		open_ledger(frm);
	},
	amount:(frm)=>{
		calculate_balance(frm);
	},
	select_cheque_lot: (frm)=>{
		fetch_cheque_lot(frm)
	},
	is_opening: (frm)=>{
		if(frm.doc.is_opening == 1){
			frm.set_df_property('od_outstanding_amount', 'read_only', 0);
		}else{
			frm.set_df_property('od_outstanding_amount', 'read_only', 1);
		}
	}
});

var set_party_type = (frm)=>{
	cur_frm.set_query('party_type', (frm)=> {
		return {
			'filters': {
				'name': 'Supplier'
			}
		};
	});
}

var fetch_cheque_lot = (frm)=>{
	if(frm.doc.select_cheque_lot) {
	   frappe.call({
		   method: "erpnext.accounts.doctype.cheque_lot.cheque_lot.get_cheque_no_and_date",
		   args: {
			   'name': frm.doc.select_cheque_lot
		   },
		   callback: function(r){
			   console.log(r.message)
			   if (r.message) {
				   cur_frm.set_value("cheque_no", r.message[0].reference_no);
				   cur_frm.set_value("cheque_date", r.message[1].reference_date);
				   cur_frm.refresh_field('cheque_no')
				   cur_frm.refresh_field('cheque_date')
			   }
		   }
	   });
   }
}

var calculate_balance=(frm)=>{
   if (frm.doc.amount > 0 ){
	   cur_frm.set_value("balance_amount",frm.doc.amount)
	   cur_frm.set_value("adjusted_amount",0)
   }
}
var open_ledger = (frm)=>{
	// if (cint(frm.doc.is_opening) == 1) return
	if (frm.doc.docstatus === 1) {
		frm.add_custom_button(
			__("Journal Entry"),
			function () {
			frappe.route_options = {
				name: frm.doc.journal_entry
			};
			frappe.set_route("List", "Journal Entry");
			},
			__("View")
		);
	}
}