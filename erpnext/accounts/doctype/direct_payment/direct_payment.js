// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Direct Payment', {
	onload: function(frm) {
		frm.toggle_display("party_type", 0);
		frm.toggle_display("party", 0);

		cur_frm.set_query("select_cheque_lot", function(){
			return 	{
				"filters":[
					["status", "!=", "Used"],
					["docstatus", "=", "1"],
				]
			}
		});

		frm.set_query('branch', function(doc, cdt, cdn) {
			return {
				filters: {
					"is_disabled": 0
				}
			};
		});
	},
	refresh: function(frm) {
		cur_frm.set_query("debit_account", function(){
			return {
				"filters": [
					["is_group", "=", "0"],					
				]
			}
		});
		cur_frm.set_query("credit_account", function(){
			var items = frm.doc.item || [];
			var party_types = items.filter(function(val){return val.party_type}).map(function(obj){return obj.party_type});
			party_types = party_types.filter((item, i, ar) => ar.indexOf(item) === i);
			return {
				query: "erpnext.accounts.doctype.direct_payment.direct_payment.get_credit_account",
				filters: {
					branch: frm.doc.branch,
					payment_type: frm.doc.payment_type,
					party_types: party_types
				}
			};
		});
		if(!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today())
		}
		if (frm.doc.party_type == "Customer"){
			cur_frm.set_query("party", function() {
				return {
					"filters": {
						"inter_company": 1
					}
				}
			 });
		}
		frm.fields_dict['item'].grid.get_field('account').get_query = function(){
			return{
				filters: {
					'is_group': 0
				}
			}
		};
		if(frm.doc.docstatus===1){
			frm.add_custom_button(__('Accounting Ledger'), function(){
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

		enable_disable(frm);
	},
	"credit_account": function(frm){
		var account = frm.doc.credit_account;
		check_party_requirement(frm, account);
	},
	"debit_account": function(frm){
		var account = frm.doc.debit_account;
		check_party_requirement(frm, account);
	},
	"select_cheque_lot": function(frm){
		if(frm.doc.select_cheque_lot) {
			frappe.call({
				method: "erpnext.accounts.doctype.cheque_lot.cheque_lot.get_cheque_no_and_date",
				args: {
					'name': frm.doc.select_cheque_lot
				},
				callback: function(r){
					if(r.message) {
						cur_frm.set_value("cheque_no", r.message[0].reference_no);
						cur_frm.set_value("cheque_date", r.message[1].reference_date);
					}
				}
			});	
		}
	},
	"payment_type": function(frm){
		if(frm.doc.payment_type == "Receive"){
				frappe.model.get_value('Branch', {'name': frm.doc.branch}, 'revenue_bank_account',
				function(d) {
					cur_frm.set_value("debit_account",d.revenue_bank_account);
				});
		}
		// Commented by SHIV on 2021/09/22
		// if(frm.doc.payment_type == "Payment"){
		// 		frappe.model.get_value('Branch', {'name': frm.doc.branch}, 'expense_bank_account',
		// 			function(d) {
		// 			cur_frm.set_value("credit_account",d.expense_bank_account);
		// 		});
		// }
		calculate_tds(frm);
	},
	"amount": function(frm) {
		frm.set_value("taxable_amount", parseFloat(frm.doc.amount))
		calculate_tds(frm);
	},
	"tds_percent": function(frm) {
		calculate_tds(frm);
		var net_amt = 0.00, tds_amt = 0.00;
		frm.doc.multiple_account.forEach(function(d) {
			net_amt += d.amount;
		});
		console.log(frm.doc.tds_percent);
		if(frm.doc.tds_percent < 1 || frm.doc.tds_percent == ""){
			cur_frm.set_value("tds_account", "");
			cur_frm.set_value("tds_amount", 0.00);
		}else{
			tds_amt = parseFloat(frm.doc.tds_percent) * parseFloat(d.net_amt) / 100;
		}
		frm.set_value("tds_amount", tds_amt);
		frm.set_value("net_amount", net_amt);
		cur_frm.set_df_property("tds_account", "reqd", (frm.doc.tds_percent > 0)? 1:0);
	},
	"taxable_amount": function(frm) {
		calculate_tds(frm);
	},
	"tds_amount": function(frm){
		frm.set_value("net_amount", parseFloat(frm.doc.amount) - parseFloat(frm.doc.tds_amount))
	},
	//added new
	// "party_type": function(frm){
	// 	if (frm.doc.party_type == 'Employee'){
	// 		frm.set_query("party",()=>{
	// 			return {
	// 				query:"erpnext.accounts.doctype.direct_payment.direct_payment.get_salary_advance",
	// 				filters:{"party_type":frm.doc.party_type, "account":frm.doc.credit_account}
	// 			}
	// 		})
	// 	}
	// },
	//end new
	
	"branch": function(frm) {
		frappe.model.get_value('Branch', {'name': frm.doc.branch}, 'cost_center',
						  function(d) {
							cur_frm.set_value("cost_center",d.cost_center);
						});
		if(frm.doc.payment_type == "Receive"){
			frappe.model.get_value('Branch', {'name': frm.doc.branch}, 'revenue_bank_account',
			  function(d) {
				cur_frm.set_value("debit_account",d.revenue_bank_account);
			});
		}
		// Commented by SHIV on 2021/09/22
		// if(frm.doc.payment_type == "Payment"){
		// 	frappe.model.get_value('Branch', {'name': frm.doc.branch}, 'expense_bank_account',
		// 	  function(d) {
		// 	    cur_frm.set_value("credit_account",d.expense_bank_account);
		// 	});
		// }
	},
	"party": function(frm) {
		frm.set_value("pay_to_recd_from", frm.doc.party);
	},
	// "party": function(frm){
	// 	get_salary_advance(frm); //added new here
	// }
	use_check_lot: function(frm){
		enable_disable(frm);
	},
	cheque_no: function(frm){
		enable_disable(frm);
	},
	cheque_date: function(frm){
		enable_disable(frm);
	}
});

cur_frm.fields_dict['item'].grid.get_field('cost_center').get_query = function(frm, cdt, cdn) {
	return {
		filters: {
			"center_category": 'Course',
			"is_disabled": 0
		}
	}
}

var enable_disable = function(frm){
	if(frm.doc.use_check_lot){
		frm.toggle_reqd(['cheque_no','cheque_date'], frm.doc.use_check_lot);
	} else {
		frm.toggle_reqd(['cheque_date'], frm.doc.cheque_no);
		frm.toggle_reqd(['cheque_no'], frm.doc.cheque_date);
	}
}

function roundOff(num) {    
    return +(Math.round(num + "e+2")  + "e-2");
}

function calculate_tds(frm) {
	frappe.call({
		method: "erpnext.accounts.doctype.direct_payment.direct_payment.get_tds_account",
		args: {
			percent: frm.doc.tds_percent,
			payment_type: frm.doc.payment_type
		},
		callback: function(r) {
			if(r.message) {
				frm.set_value("tds_account", r.message);
				cur_frm.refresh_field("tds_account");
			}
		}
	})
}
//added new here
// function get_salary_advance(frm){
// 	method: "erpnext.accounts.doctype.direct_payment.direct_payment.get_salary_advance",
// 	args:{
// 		party_type: frm.doc.
// 	}
//}
//end new

frappe.ui.form.on("Direct Payment Item", {
    "party_type": function(frm, cdt, cdn){
		frappe.model.set_value(cdt, cdn, "party", "");
		},
	"amount": function(frm, cdt, cdn){
		var item = frappe.get_doc(cdt,cdn);
		frappe.model.set_value(cdt, cdn, "taxable_amount", item.amount);
		calculate_total(frm, cdt, cdn);
		},
	"taxable_amount": function(frm, cdt, cdn){
		calculate_total(frm, cdt, cdn);
		},
	"tds_amount": function(frm, cdt, cdn){
		calculate_total(frm, cdt, cdn);
		},
	"tds_applicable": function(frm, cdt, cdn){
		var item = frappe.get_doc(cdt,cdn)
		if(!item.tds_applicable){
			frappe.model.set_value(cdt, cdn, "tds_amount", 0.00);
			frappe.model.set_value(cdt, cdn, "net_amount", item.amount);
		}
		calculate_total(frm, cdt, cdn);
	}
});

function calculate_total(frm, cdt, cdn){
	var item = frappe.get_doc(cdt,cdn)
	if(frm.doc.tds_percent > 0 && item.tds_applicable){
		frappe.model.set_value(cdt, cdn, "tds_amount", parseFloat(frm.doc.tds_percent) * parseFloat(item.taxable_amount) / 100 );
	}else{
		frappe.model.set_value(cdt, cdn, "tds_amount", 0.00);
	}
	
	frappe.model.set_value(cdt, cdn, "net_amount", parseFloat(item.amount) - parseFloat(item.tds_amount));
	var gross_amount=0, total_taxable_amount=0, total_net_amount=0, total_tds_amount=0;
	frm.doc.item.forEach(function(d) {
		gross_amount += d.amount;
		total_net_amount += d.net_amount;
		total_taxable_amount += d.taxable_amount;
		total_tds_amount += d.tds_amount;
	});
	frm.set_value("amount", gross_amount);
	frm.set_value("taxable_amount", total_taxable_amount);
	frm.set_value("net_amount", total_net_amount);
	frm.set_value("tds_amount", total_tds_amount);	
}

function check_party_requirement(frm, account){
	if(account){
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Account",
				name: account,
			},
			callback(r) {
				if(r.message) {
					var doc = r.message;
					if(doc.account_type == "Payable" || doc.account_type == "Receivable"){
						frm.toggle_display("party_type", 1);
						frm.toggle_display("party", 1);
						// cur_frm.set_df_property("party_type", "reqd", 1)
						// cur_frm.set_df_property("party", "reqd", 1)
						cur_frm.set_df_property("party_type", "reqd", 0)
						cur_frm.set_df_property("party", "reqd", 0)
					}else{
						frm.toggle_display("party_type", 0);
						frm.toggle_display("party", 0);
						cur_frm.set_df_property("party_type", "reqd", 0)
						cur_frm.set_df_property("party", "reqd", 0)
					}
				}
			}
		});
	}
}