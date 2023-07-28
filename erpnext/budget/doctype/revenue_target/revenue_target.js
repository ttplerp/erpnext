// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Revenue Target', {
	onload: function(frm){
		frm.set_query("account", "revenue_target_account", function() {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0
				}
			};
		});
		frm.set_query("cost_center", function(){
			return {
				"filters": [
					["is_group","=", "0"]
						
				]
			}
		});
	},
	refresh: function(frm) {
		if (frm.doc.docstatus == 1){
			frm.add_custom_button(__("Achievement Report"), function(){
			var fy = frappe.model.get_doc("Fiscal Year", frm.doc.fiscal_year);
			var y_start_date = y_end_date = "";
				
			if (fy) {
				y_start_date = fy.year_start_date;
				y_end_date   = fy.year_end_date;
			}
				
			frappe.route_options = {
				fiscal_year: frm.doc.fiscal_year,
				from_date: y_start_date,
				to_date: y_end_date
			};
			frappe.set_route("query-report", "Revenue Target");
				}
			);
			
		}
	},

	branch: function(frm){
		frm.clear_table("revenue_target_account");
		frm.refresh_field("revenue_target_account");
	},

	get_accounts: function(frm){
		return frappe.call({
			method: "get_accounts",
			doc:frm.doc,
			callback: function(r, rt){
				frm.refresh_field("revenue_target_account");
				frm.refresh_fields();
			},
			freeze: true,
			freeze_message: "Loading Income Accounts..... Please Wait"
		});
	},
});

frappe.ui.form.on('Revenue Target Account',{
	"january": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"february": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"march": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"april": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"may": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"june": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"july": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"august": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"september": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"october": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"november": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
	"december": function(frm, cdt, cdn) {
		set_initial_revenue_target(frm, cdt, cdn);
	},
});

var set_initial_revenue_target=(frm,cdt,cdn)=>{
	frappe.call({
		method:"set_initial_revenue_target",
		doc: frm.doc,
		callback: function(r) {
			frm.refresh_field('target_amount');
			frm.refresh_field('tot_target_amount');
			frm.refresh_fields('revenue_target_account');
		}
	})
	// var item = locals[cdt][cdn]
	// item.target_amount = flt(item.january)+ flt(item.february) + flt(item.march) + flt(item.april)+ flt(item.may) +flt(item.june) +flt(item.july) +flt(item.august) + flt(item.september) +flt(item.october) +flt(item.november) +flt(item.december) 

	// frm.refresh_field('revenue_target_account')

	// let amount = 0
	// frm.doc.revenue_target_account.forEach(row => {
	// 	amount += flt(row.target_amount)

	// });
	// frm.set_value('tot_target_amount', amount)
	// frm.refresh_field('tot_target_amount')
}
