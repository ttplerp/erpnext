// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.accounts");
frappe.provide("erpnext.journal_entry");

{% include "erpnext/public/js/controllers/cheque_details.js" %};

frappe.ui.form.on("Journal Entry", {
	setup: function(frm) {
		frm.add_fetch("bank_account", "account", "account");
		frm.ignore_doctypes_on_cancel_all = ['Sales Invoice', 'Purchase Invoice'];
		draw_tds_table(frm)
	},

	onload:function(frm){
		draw_tds_table(frm)
	},

	refresh: function(frm) {
		erpnext.toggle_naming_series();

		if(frm.doc.docstatus > 0) {
			frm.add_custom_button(__('Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": moment(frm.doc.modified).format('YYYY-MM-DD'),
					"company": frm.doc.company,
					"finance_book": frm.doc.finance_book,
					"group_by": '',
					"show_cancelled_entries": frm.doc.docstatus === 2
				};
				frappe.set_route("query-report", "General Ledger");
			}, __('View'));
		}

		if(frm.doc.docstatus==1) {
			frm.add_custom_button(__('Reverse Journal Entry'), function() {
				return erpnext.journal_entry.reverse_journal_entry(frm);
			}, __('Actions'));
		}

		if (frm.doc.__islocal) {
			frm.add_custom_button(__('Quick Entry'), function() {
				return erpnext.journal_entry.quick_entry(frm);
			});
		}

		// hide /unhide fields based on currency
		erpnext.journal_entry.toggle_fields_based_on_currency(frm);

		if ((frm.doc.voucher_type == "Inter Company Journal Entry") && (frm.doc.docstatus == 1) && (!frm.doc.inter_company_journal_entry_reference)) {
			frm.add_custom_button(__("Create Inter Company Journal Entry"),
				function() {
					frm.trigger("make_inter_company_journal_entry");
				}, __('Make'));
		}
		draw_tds_table(frm)
	},

	make_inter_company_journal_entry: function(frm) {
		var d = new frappe.ui.Dialog({
			title: __("Select Company"),
			fields: [
				{
					'fieldname': 'company',
					'fieldtype': 'Link',
					'label': __('Company'),
					'options': 'Company',
					"get_query": function () {
						return {
							filters: [
								["Company", "name", "!=", frm.doc.company]
							]
						};
					},
					'reqd': 1
				}
			],
		});
		d.set_primary_action(__('Create'), function() {
			d.hide();
			var args = d.get_values();
			frappe.call({
				args: {
					"name": frm.doc.name,
					"voucher_type": frm.doc.voucher_type,
					"company": args.company
				},
				method: "erpnext.accounts.doctype.journal_entry.journal_entry.make_inter_company_journal_entry",
				callback: function (r) {
					if (r.message) {
						var doc = frappe.model.sync(r.message)[0];
						frappe.set_route("Form", doc.doctype, doc.name);
					}
				}
			});
		});
		d.show();
	},

	multi_currency: function(frm) {
		erpnext.journal_entry.toggle_fields_based_on_currency(frm);
	},

	posting_date: function(frm) {
		if(!frm.doc.multi_currency || !frm.doc.posting_date) return;

		$.each(frm.doc.accounts || [], function(i, row) {
			erpnext.journal_entry.set_exchange_rate(frm, row.doctype, row.name);
		})
	},

	company: function(frm) {
		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "Company",
				filters: {"name": frm.doc.company},
				fieldname: "cost_center"
			},
			callback: function(r){
				if(r.message){
					$.each(frm.doc.accounts || [], function(i, jvd) {
						frappe.model.set_value(jvd.doctype, jvd.name, "cost_center", r.message.cost_center);
					});
				}
			}
		});

		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
	},

	voucher_type: function(frm){
		
		if(!frm.doc.company) return null;

		frm.trigger("naming_series_value_update");/* Added by Jai */

		if((!(frm.doc.accounts || []).length) || ((frm.doc.accounts || []).length === 1 && !frm.doc.accounts[0].account)) {
			if(in_list(["Bank Entry", "Cash Entry"], frm.doc.voucher_type)) {
				return frappe.call({
					type: "GET",
					method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_default_bank_cash_account",
					args: {
						"account_type": (frm.doc.voucher_type=="Bank Entry" ?
							"Bank" : (frm.doc.voucher_type=="Cash Entry" ? "Cash" : null)),
						"company": frm.doc.company
					},
					callback: function(r) {
						if(r.message) {
							// If default company bank account not set
							if(!$.isEmptyObject(r.message)){
								update_jv_details(frm.doc, [r.message]);
							}
						}
					}
				});
			}
		}

	},

	naming_series_value_update: function(frm){
		if (frm.doc.voucher_type == 'Journal Entry' || frm.doc.voucher_type == 'Opening Entry' || frm.doc.voucher_type == 'Depreciation Entry') {
			cur_frm.set_value("naming_series", "Journal Voucher");
		} else if (frm.doc.voucher_type == 'Bank Entry' && !in_list(['Bank Payment Voucher','Bank Receipt Voucher'], frm.doc.naming_series)) {
			cur_frm.set_value("naming_series", "");
		} else if (frm.doc.voucher_type == 'Cash Entry' && !in_list(['Cash Payment Voucher','Cash Receipt Voucher'], frm.doc.naming_series)) {
			cur_frm.set_value("naming_series", "");
		} else if (frm.doc.voucher_type == 'Contra Entry') {
			cur_frm.set_value("naming_series", "Contra Entry");
		}
	},

	from_template: function(frm){
		if (frm.doc.from_template){
			frappe.db.get_doc("Journal Entry Template", frm.doc.from_template)
				.then((doc) => {
					frappe.model.clear_table(frm.doc, "accounts");
					frm.set_value({
						"company": doc.company,
						"voucher_type": doc.voucher_type,
						"naming_series": doc.naming_series,
						"is_opening": doc.is_opening,
						"multi_currency": doc.multi_currency
					})
					update_jv_details(frm.doc, doc.accounts);
				});
		}
	},

	apply_tds: function(frm){
		$.each(frm.doc.accounts || [], function(i, row) {
			if(row.add_deduct_tax){
				frappe.model.set_value(row.doctype, row.name, "apply_tds", cint(frm.doc.apply_tds));
			}
		})
		draw_tds_table(frm)
	},

	tax_withholding_category: function(frm){
		$.each(frm.doc.accounts || [], function(i, row) {
			if(row.add_deduct_tax){
				erpnext.journal_entry.set_tds_account(frm, row.doctype, row.name);
			}
		})
	}
});

var draw_tds_table = function(frm){
	let is_tds = false
	let i = 1
	let row = "<tbody><tr><td style='width:4%;'><div style='height:15px;width:15px;border-radius:5px;background:#ebeef0;'></div></td>"
		row += "<td style='width:4%;'>No.</td> <td style='width:16.8%;'> Accounts </td><td style='width:16.8%;'> Party </td>"
		row += "<td style='width:16.8%;'> Cost Center </td> <td style='width:16.8%;text-align:right;'> Debit </td><td style='width:16.8%;text-align:right;'>Credit</td>"
		row += "<td style='width:5%;text-align:center;'><i class='fa fa-gear'></i></td></tr></tbody>"
		row += "<tbody>"
	frm.doc.accounts.map(v=>{
		if (flt(v.apply_tds) == 1){
			is_tds = true
			row += "<tr><th style='width:4%;'><div style='height:13px;width:13px;border-radius:3px;background:#ebeef0;'></div></th>"
			row	+=	"<th style='width:4%;'>"+i+"</th> "
			row	+=	"<th style='width:16.8%;'> "+ v.tax_account+" </th>"
			row	+=	"<th style='width:16.8%;'> "+ v.party +" </th>"
			row	+= "<th style='width:16.8%;'>"+ v.cost_center+" </th>"
			row	+=	"<th style='width:16.8%;text-align:right;'> 0 </th>"
			row	+=	"<th style='width:16.8%;text-align:right;'>"+v.tax_amount+"</th> <th style='width:8%;'></th></tr>"
			i += 1
		}
	})
	row += "</tbody>"
	if(is_tds)$(cur_frm.fields_dict.tds_table.wrapper).html('<table class="table table-bordered">'+row+'</table>');
	else $(cur_frm.fields_dict.tds_table.wrapper).html('');

	// frm.refresh_field("tds_table")
}

var update_jv_details = function(doc, r) {
	$.each(r, function(i, d) {
		var row = frappe.model.add_child(doc, "Journal Entry Account", "accounts");
		row.account = d.account;
		row.balance = d.balance;
	});
	refresh_field("accounts");
}

erpnext.accounts.JournalEntry = class JournalEntry extends frappe.ui.form.Controller {
	onload() {
		this.load_defaults();
		this.setup_queries();
		this.setup_balance_formatter();
		erpnext.accounts.dimensions.setup_dimension_filters(this.frm, this.frm.doctype);
	}

	onload_post_render() {
		cur_frm.get_field("accounts").grid.set_multiple_add("account");
	}

	load_defaults() {
		//this.frm.show_print_first = true;
		if(this.frm.doc.__islocal && this.frm.doc.company) {
			frappe.model.set_default_values(this.frm.doc);
			$.each(this.frm.doc.accounts || [], function(i, jvd) {
				frappe.model.set_default_values(jvd);
			});
			var posting_date = this.frm.doc.posting_date;
			if(!this.frm.doc.amended_from) this.frm.set_value('posting_date', posting_date || frappe.datetime.get_today());
		}
	}

	setup_queries() {
		var me = this;

		me.frm.set_query("account", "accounts", function(doc, cdt, cdn) {
			return erpnext.journal_entry.account_query(me.frm);
		});

		me.frm.set_query("party_type", "accounts", function(doc, cdt, cdn) {
			const row = locals[cdt][cdn];

			return {
				query: "erpnext.setup.doctype.party_type.party_type.get_party_type",
				filters: {
					'account': row.account
				}
			}
		});

		me.frm.set_query("reference_name", "accounts", function(doc, cdt, cdn) {
			var jvd = frappe.get_doc(cdt, cdn);

			// journal entry
			if(jvd.reference_type==="Journal Entry") {
				frappe.model.validate_missing(jvd, "account");
				return {
					query: "erpnext.accounts.doctype.journal_entry.journal_entry.get_against_jv",
					filters: {
						account: jvd.account,
						party: jvd.party
					}
				};
			}

			var out = {
				filters: [
					[jvd.reference_type, "docstatus", "=", 1]
				]
			};

			if(in_list(["Sales Invoice", "Purchase Invoice"], jvd.reference_type)) {
				out.filters.push([jvd.reference_type, "outstanding_amount", "!=", 0]);
				// Filter by cost center
				if(jvd.cost_center) {
					out.filters.push([jvd.reference_type, "cost_center", "in", ["", jvd.cost_center]]);
				}
				// account filter
				frappe.model.validate_missing(jvd, "account");
				var party_account_field = jvd.reference_type==="Sales Invoice" ? "debit_to": "credit_to";
				out.filters.push([jvd.reference_type, party_account_field, "=", jvd.account]);

				if (in_list(['Debit Note', 'Credit Note'], doc.voucher_type)) {
					out.filters.push([jvd.reference_type, "is_return", "=", 1]);
				}
			}

			if(in_list(["Sales Order", "Purchase Order"], jvd.reference_type)) {
				// party_type and party mandatory
				frappe.model.validate_missing(jvd, "party_type");
				frappe.model.validate_missing(jvd, "party");

				out.filters.push([jvd.reference_type, "per_billed", "<", 100]);
			}

			if(jvd.party_type && jvd.party) {
				var party_field = "";
				if(jvd.reference_type.indexOf("Sales")===0) {
					var party_field = "customer";
				} else if (jvd.reference_type.indexOf("Purchase")===0) {
					var party_field = "supplier";
				}

				if (party_field) {
					out.filters.push([jvd.reference_type, party_field, "=", jvd.party]);
				}
			}

			return out;
		});


	}

	setup_balance_formatter() {
		const formatter = function(value, df, options, doc) {
			var currency = frappe.meta.get_field_currency(df, doc);
			var dr_or_cr = value ? ('<label>' + (value > 0.0 ? __("Dr") : __("Cr")) + '</label>') : "";
			return "<div style='text-align: right'>"
				+ ((value==null || value==="") ? "" : format_currency(Math.abs(value), currency))
				+ " " + dr_or_cr
				+ "</div>";
		};
		this.frm.fields_dict.accounts.grid.update_docfield_property('balance', 'formatter', formatter);
		this.frm.fields_dict.accounts.grid.update_docfield_property('party_balance', 'formatter', formatter);
	}

	reference_name(doc, cdt, cdn) {
		var d = frappe.get_doc(cdt, cdn);

		if(d.reference_name) {
			if (d.reference_type==="Purchase Invoice" && !flt(d.debit)) {
				this.get_outstanding('Purchase Invoice', d.reference_name, doc.company, d);
			} else if (d.reference_type==="Sales Invoice" && !flt(d.credit)) {
				this.get_outstanding('Sales Invoice', d.reference_name, doc.company, d);
			} else if (d.reference_type==="Journal Entry" && !flt(d.credit) && !flt(d.debit)) {
				this.get_outstanding('Journal Entry', d.reference_name, doc.company, d);
			}
		}
	}

	get_outstanding(doctype, docname, company, child, due_date) {
		var me = this;
		var args = {
			"doctype": doctype,
			"docname": docname,
			"party": child.party,
			"account": child.account,
			"account_currency": child.account_currency,
			"company": company
		}

		return frappe.call({
			method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_outstanding",
			args: { args: args},
			callback: function(r) {
				if(r.message) {
					$.each(r.message, function(field, value) {
						frappe.model.set_value(child.doctype, child.name, field, value);
					})
				}
			}
		});
	}

	accounts_add(doc, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		$.each(doc.accounts, function(i, d) {
			if(d.account && d.party && d.party_type) {
				row.account = d.account;
				row.party = d.party;
				row.party_type = d.party_type;
			}
		});

		// set difference
		if(doc.difference) {
			if(doc.difference > 0) {
				row.credit_in_account_currency = doc.difference;
				row.credit = doc.difference;
			} else {
				row.debit_in_account_currency = -doc.difference;
				row.debit = -doc.difference;
			}
		}
		cur_frm.cscript.update_totals(doc);

		erpnext.accounts.dimensions.copy_dimension_from_first_row(this.frm, cdt, cdn, 'accounts');
	}

};

cur_frm.script_manager.make(erpnext.accounts.JournalEntry);

cur_frm.cscript.update_totals = function(doc) {
	var td=0.0; var tc =0.0; var tax_amount=0.0, tax_dr=0.0, tax_cr=0.0;
	var accounts = doc.accounts || [];
	for(var i in accounts) {
		td += flt(accounts[i].debit, precision("debit", accounts[i]));
		tc += flt(accounts[i].credit, precision("credit", accounts[i]));
		if((doc.apply_tds) && cint(accounts[i].apply_tds) && accounts[i].add_deduct_tax){
			tax_amount = flt(accounts[i].tax_amount);
			if(accounts[i].add_deduct_tax == "Add"){
				tax_cr += (flt(accounts[i].credit)) ? tax_amount : 0;
				tax_dr += (flt(accounts[i].debit)) ? tax_amount : 0;
			} else {
				tax_dr += (flt(accounts[i].credit)) ? tax_amount : 0;
				tax_cr += (flt(accounts[i].debit)) ? tax_amount : 0;
			}
		}
	}
	var doc = locals[doc.doctype][doc.name];
	doc.total_debit = td + tax_dr;
	doc.total_credit = tc + tax_cr;
	doc.difference = flt(((td+tax_dr) - (tc+tax_cr)), precision("difference"));
	refresh_many(['total_debit','total_credit','difference']);
}

cur_frm.cscript.get_balance = function(doc,dt,dn) {
	cur_frm.cscript.update_totals(doc);
	cur_frm.call('get_balance', null, () => { cur_frm.refresh(); });
}

cur_frm.cscript.validate = function(doc,cdt,cdn) {
	cur_frm.cscript.update_totals(doc);
}

frappe.ui.form.on("Journal Entry Account", {
	party: function(frm, cdt, cdn) {
		var d = frappe.get_doc(cdt, cdn);
		if(!d.account && d.party_type && d.party) {
			if(!frm.doc.company) frappe.throw(__("Please select Company"));
			return frm.call({
				method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_party_account_and_balance",
				child: d,
				args: {
					company: frm.doc.company,
					party_type: d.party_type,
					party: d.party,
					cost_center: d.cost_center
				}
			});
		}
	},
	cost_center: function(frm, dt, dn) {
		erpnext.journal_entry.set_account_balance(frm, dt, dn);
	},

	account: function(frm, dt, dn) {
		erpnext.journal_entry.set_account_balance(frm, dt, dn);
	},

	debit_in_account_currency: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "taxable_amount_in_account_currency",
				flt(row.debit_in_account_currency) || flt(row.credit_in_account_currency));
		erpnext.journal_entry.set_exchange_rate(frm, cdt, cdn);
	},

	credit_in_account_currency: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "taxable_amount_in_account_currency",
				flt(row.debit_in_account_currency) || flt(row.credit_in_account_currency));
		erpnext.journal_entry.set_exchange_rate(frm, cdt, cdn);
	},

	debit: function(frm, dt, dn) {
		cur_frm.cscript.update_totals(frm.doc);
	},

	credit: function(frm, dt, dn) {
		cur_frm.cscript.update_totals(frm.doc);
	},

	exchange_rate: function(frm, cdt, cdn) {
		var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
		var row = locals[cdt][cdn];

		if(row.account_currency == company_currency || !frm.doc.multi_currency) {
			frappe.model.set_value(cdt, cdn, "exchange_rate", 1);
		}

		erpnext.journal_entry.set_debit_credit_in_company_currency(frm, cdt, cdn);
		erpnext.journal_entry.set_tax_in_company_currency(frm, cdt, cdn);
	},

	// following methods added by SHIV on 2022/09/17
	apply_tds: function(frm, cdt, cdn){
		erpnext.journal_entry.set_tds_account(frm, cdt, cdn);
		cur_frm.cscript.update_totals(frm.doc);
	},

	add_deduct_tax: function(frm, cdt, cdn) {
		erpnext.journal_entry.set_tax_in_company_currency(frm, cdt, cdn);
		cur_frm.cscript.update_totals(frm.doc);
	},

	rate: function(frm, cdt, cdn) {
		erpnext.journal_entry.set_tax_in_company_currency(frm, cdt, cdn);
		cur_frm.cscript.update_totals(frm.doc);
	},
	
	taxable_amount_in_account_currency: function(frm, cdt, cdn){
		erpnext.journal_entry.set_tax_in_company_currency(frm, cdt, cdn);
		cur_frm.cscript.update_totals(frm.doc);
	},

	tax_amount: function(frm, cdt, cdn){
		cur_frm.cscript.update_totals(frm.doc);
	}
})

frappe.ui.form.on("Journal Entry Account", "accounts_remove", function(frm) {
	cur_frm.cscript.update_totals(frm.doc);
});

$.extend(erpnext.journal_entry, {
	toggle_fields_based_on_currency: function(frm) {
		var fields = ["currency_section", "account_currency", "exchange_rate", "debit", "credit"];

		var grid = frm.get_field("accounts").grid;
		if(grid) grid.set_column_disp(fields, frm.doc.multi_currency);

		// dynamic label
		var field_label_map = {
			"debit_in_account_currency": "Debit",
			"credit_in_account_currency": "Credit"
		};

		$.each(field_label_map, function (fieldname, label) {
			frm.fields_dict.accounts.grid.update_docfield_property(
				fieldname,
				'label',
				frm.doc.multi_currency ? (label + " in Account Currency") : label
			);
		})
	},

	set_debit_credit_in_company_currency: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];

		frappe.model.set_value(cdt, cdn, "debit",
			flt(flt(row.debit_in_account_currency)*row.exchange_rate, precision("debit", row)));

		frappe.model.set_value(cdt, cdn, "credit",
			flt(flt(row.credit_in_account_currency)*row.exchange_rate, precision("credit", row)));

		cur_frm.cscript.update_totals(frm.doc);
	},

	// added by SHIV on 2022/09/17
	set_tax_in_company_currency: function(frm, cdt, cdn) {
		console.log("set_tax_in_company_currency");
		var row = locals[cdt][cdn], tax_amount = 0.0;

		frappe.model.set_value(cdt, cdn, "taxable_amount",
			flt(flt(row.taxable_amount_in_account_currency)*row.exchange_rate, precision("taxable_amount", row)));

		tax_amount = flt(row.taxable_amount_in_account_currency) * flt(row.rate) / 100;
		tax_amount = (cint(frm.doc.apply_tds) && cint(row.apply_tds) && row.add_deduct_tax) ? flt(tax_amount) : 0;

		frappe.model.set_value(cdt, cdn, "tax_amount_in_account_currency",
			flt(tax_amount, precision("tax_amount", row)));

		frappe.model.set_value(cdt, cdn, "tax_amount",
			flt(flt(tax_amount)*row.exchange_rate, precision("tax_amount", row)));

		cur_frm.cscript.update_totals(frm.doc);
	},

	// added by SHIV on 2022/09/21
	set_tds_account: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];

		frappe.model.set_value(cdt, cdn, "tax_account", null);
		frappe.model.set_value(cdt, cdn, "rate", 0);
		frappe.call({
			method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_tds_account",
			args: {
				tax_withholding_category: frm.doc.tax_withholding_category || null
			},
			callback: function(r){
				if(r.message){
					frappe.model.set_value(cdt, cdn, "tax_account", r.message.tax_withholding_account);
					frappe.model.set_value(cdt, cdn, "rate", r.message.tax_withholding_rate);
				}
			}
		})
	},

	set_exchange_rate: function(frm, cdt, cdn) {
		var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
		var row = locals[cdt][cdn];

		if(row.account_currency == company_currency || !frm.doc.multi_currency) {
			row.exchange_rate = 1;
			erpnext.journal_entry.set_debit_credit_in_company_currency(frm, cdt, cdn);
			erpnext.journal_entry.set_tax_in_company_currency(frm, cdt, cdn);
		} else if (!row.exchange_rate || row.exchange_rate == 1 || row.account_type == "Bank") {
			frappe.call({
				method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_exchange_rate",
				args: {
					posting_date: frm.doc.posting_date,
					account: row.account,
					account_currency: row.account_currency,
					company: frm.doc.company,
					reference_type: cstr(row.reference_type),
					reference_name: cstr(row.reference_name),
					debit: flt(row.debit_in_account_currency),
					credit: flt(row.credit_in_account_currency),
					exchange_rate: row.exchange_rate
				},
				callback: function(r) {
					if(r.message) {
						row.exchange_rate = r.message;
						erpnext.journal_entry.set_debit_credit_in_company_currency(frm, cdt, cdn);
						erpnext.journal_entry.set_tax_in_company_currency(frm, cdt, cdn);
					}
				}
			})
		} else {
			erpnext.journal_entry.set_debit_credit_in_company_currency(frm, cdt, cdn);
			erpnext.journal_entry.set_tax_in_company_currency(frm, cdt, cdn);
		}
		refresh_field("exchange_rate", cdn, "accounts");
	},

	quick_entry: function(frm) {
		var naming_series_options = frm.fields_dict.naming_series.df.options;
		var naming_series_default = frm.fields_dict.naming_series.df.default || naming_series_options.split("\n")[0];

		var dialog = new frappe.ui.Dialog({
			title: __("Quick Journal Entry"),
			fields: [
				{fieldtype: "Currency", fieldname: "debit", label: __("Amount"), reqd: 1},
				{fieldtype: "Link", fieldname: "debit_account", label: __("Debit Account"), reqd: 1,
					options: "Account",
					get_query: function() {
						return erpnext.journal_entry.account_query(frm);
					}
				},
				{fieldtype: "Link", fieldname: "credit_account", label: __("Credit Account"), reqd: 1,
					options: "Account",
					get_query: function() {
						return erpnext.journal_entry.account_query(frm);
					}
				},
				{fieldtype: "Date", fieldname: "posting_date", label: __("Date"), reqd: 1,
					default: frm.doc.posting_date},
				{fieldtype: "Small Text", fieldname: "user_remark", label: __("User Remark")},
				{fieldtype: "Select", fieldname: "naming_series", label: __("Series"), reqd: 1,
					options: naming_series_options, default: naming_series_default},
			]
		});

		dialog.set_primary_action(__("Save"), function() {
			var btn = this;
			var values = dialog.get_values();

			frm.set_value("posting_date", values.posting_date);
			frm.set_value("user_remark", values.user_remark);
			frm.set_value("naming_series", values.naming_series);

			// clear table is used because there might've been an error while adding child
			// and cleanup didn't happen
			frm.clear_table("accounts");

			// using grid.add_new_row() to add a row in UI as well as locals
			// this is required because triggers try to refresh the grid

			var debit_row = frm.fields_dict.accounts.grid.add_new_row();
			frappe.model.set_value(debit_row.doctype, debit_row.name, "account", values.debit_account);
			frappe.model.set_value(debit_row.doctype, debit_row.name, "debit_in_account_currency", values.debit);

			var credit_row = frm.fields_dict.accounts.grid.add_new_row();
			frappe.model.set_value(credit_row.doctype, credit_row.name, "account", values.credit_account);
			frappe.model.set_value(credit_row.doctype, credit_row.name, "credit_in_account_currency", values.debit);

			frm.save();

			dialog.hide();
		});

		dialog.show();
	},

	account_query: function(frm) {
		var filters = {
			company: frm.doc.company,
			is_group: 0
		};
		if(!frm.doc.multi_currency) {
			$.extend(filters, {
				account_currency: frappe.get_doc(":Company", frm.doc.company).default_currency
			});
		}
		return { filters: filters };
	},

	reverse_journal_entry: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.journal_entry.journal_entry.make_reverse_journal_entry",
			frm: cur_frm
		})
	},
});

$.extend(erpnext.journal_entry, {
	set_account_balance: function(frm, dt, dn) {
		var d = locals[dt][dn];
		if(d.account) {
			if(!frm.doc.company) frappe.throw(__("Please select Company first"));
			if(!frm.doc.posting_date) frappe.throw(__("Please select Posting Date first"));

			return frappe.call({
				method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_account_balance_and_party_type",
				args: {
					account: d.account,
					date: frm.doc.posting_date,
					company: frm.doc.company,
					debit: flt(d.debit_in_account_currency),
					credit: flt(d.credit_in_account_currency),
					exchange_rate: d.exchange_rate,
					cost_center: d.cost_center
				},
				callback: function(r) {
					if(r.message) {
						$.extend(d, r.message);
						erpnext.journal_entry.set_debit_credit_in_company_currency(frm, dt, dn);
						refresh_field('accounts');
					}
				}
			});
		}
	},
});
