// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
//frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on('Budget', {
	onload: function(frm) {
		// if (frm.doc.__islocal) {
		// 	frappe.model.get_value('Accounts Settings', {'name': 'Accounts Settings'}, 'budget_level',
		// 		function(d) {
		// 			frm.set_value("budget_against", d.budget_level);
		// 	});
		// }
		if(frm.doc.__islocal) {
			frappe.call({
				method: "erpnext.custom_utils.get_user_info",
				args: {"user": frappe.session.user},
				callback(r) {
					cur_frm.set_value("company", r.message.company);
				}
			});
		}
			
		frm.set_query("cost_center", function() {
			return {
				filters: {
					company: frm.doc.company,
					disabled: 0,
					use_budget_from_parent: 0
				}
			}
		});

		frm.set_query("account", "accounts", function() {
			return {
				filters: {
					company: frm.doc.company,
					// report_type: "Profit and Loss",
					is_group: 0
				}
			};
		});

		frm.set_query("monthly_distribution", function() {
			return {
				filters: {
					fiscal_year: frm.doc.fiscal_year
				}
			};
		});
		//erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
	},

	refresh: function(frm) {
		frm.trigger("toggle_reqd_fields")
		frm.get_field("accounts").grid.grid_pagination.page_length = 150
	},

	budget_against: function(frm) {
		frm.trigger("set_null_value")
		frm.trigger("toggle_reqd_fields")
	},

	set_null_value: function(frm) {
		if(frm.doc.budget_against == 'Cost Center') {
			frm.set_value('project', null)
		} else {
			frm.set_value('cost_center', null)
		}
	},
	get_accounts: function(frm) {
		if(frm.doc.cost_center || frm.doc.project){
			return frappe.call({
				method: "get_accounts",
				doc: frm.doc,
				callback: function(r, rt) {
					frm.refresh_field("accounts");
					frm.refresh_fields();
				},
				freeze: true,
				freeze_message: "Loading Expense Accounts..... Please Wait"
			});
		}else{
			frappe.throw("Either Cost Center or Project is missing. ")
		}
	},
	toggle_reqd_fields: function(frm) {
		frm.toggle_reqd("cost_center", frm.doc.budget_against=="Cost Center");
		frm.toggle_reqd("project", frm.doc.budget_against=="Project");
	}
});

frappe.ui.form.on("Budget Account", {
	initial_budget: function (frm, doctype, name) {
		var d = locals[doctype][name];
		if(d.initial_budget >0){
			frappe.model.set_value(doctype, name, "budget_amount", d.initial_budget);
		}
	},
});
