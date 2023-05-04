// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Advance', {
	onload: function(frm){
		if(frm.doc.__islocal && frm.doc.project){
			set_defaults(frm.doc);
		}
	},
	
	refresh: function(frm) {
		refresh_html(frm);
		set_exchange_rate_label(frm);
		if(!frm.doc.__islocal){
			// if(frappe.model.can_read("Project")) {
				if(frm.doc.journal_entry){
					frm.add_custom_button(__('Bank Entries'), function() {
							frappe.route_options = {"name": frm.doc.journal_entry};
							frappe.set_route("List", "Journal Entry");
					}, __("View"));
				}
			// }
		}
	},
	
	project: function(frm){
		set_defaults(frm.doc);
	},
	
	currency: function(frm){
		update_advance_amount(frm);
		set_exchange_rate_label(frm);
	},
	
	exchange_rate: function(frm){
		frm.set_value("advance_amount", flt(frm.doc.advance_amount_requested)*flt(frm.doc.exchange_rate));
	},
	
	advance_amount_requested: function(frm){
		frm.set_value("advance_amount", flt(frm.doc.advance_amount_requested)*flt(frm.doc.exchange_rate));
	}
});

var set_defaults=function(doc){
	cur_frm.call({
		method: "set_defaults",
		doc:doc
	});
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

var set_exchange_rate_label = function(frm) {
	var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
	
	cur_frm.toggle_display(["exchange_rate","advance_amount"], frm.doc.currency != company_currency);

	if(frm.doc.currency && company_currency) {
		var default_label = __(frappe.meta.docfield_map[cur_frm.doctype]["exchange_rate"].label);
		cur_frm.fields_dict.exchange_rate.set_label(default_label +
				repl(" (1 %(from_currency)s = [?] %(to_currency)s)", {"from_currency": frm.doc.currency, "to_currency": company_currency}));
	}
	
	if(frm.doc.currency){
		var default_label = __(frappe.meta.docfield_map[cur_frm.doctype]["advance_amount_requested"].label);
		cur_frm.fields_dict.advance_amount_requested.set_label(default_label + repl(" (%(from_currency)s)", {"from_currency": frm.doc.currency}));
	}
	
	if(company_currency){
		var default_label1 = __(frappe.meta.docfield_map[cur_frm.doctype]["advance_amount"].label);
		var default_label2 = __(frappe.meta.docfield_map[cur_frm.doctype]["received_amount"].label);
		var default_label3 = __(frappe.meta.docfield_map[cur_frm.doctype]["paid_amount"].label);
		var default_label4 = __(frappe.meta.docfield_map[cur_frm.doctype]["adjustment_amount"].label);
		var default_label5 = __(frappe.meta.docfield_map[cur_frm.doctype]["balance_amount"].label);
		var label = repl(" (%(from_currency)s)", {"from_currency": company_currency});
		cur_frm.fields_dict.advance_amount.set_label(default_label1 + label);
		cur_frm.fields_dict.received_amount.set_label(default_label2 + label);
		cur_frm.fields_dict.paid_amount.set_label(default_label3 + label);
		cur_frm.fields_dict.adjustment_amount.set_label(default_label4 + label);
		cur_frm.fields_dict.balance_amount.set_label(default_label5 + label);
	}
}

var update_advance_amount = function(frm){
	var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;
	
	if(frm.doc.currency == company_currency){
		frm.set_value("exchange_rate", 1);
		frm.set_value("exchange_rate_original", 1);
		frm.set_value("advance_amount", frm.doc.advance_amount_requested);
	} else {
		frappe.call({
			method: "erpnext.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
			args: {
					"from_currency": frm.doc.currency,
					"to_currency": company_currency
			},
			callback: function(r) {
				if(r.message) {
						frm.set_value("exchange_rate", flt(r.message));
						frm.set_value("exchange_rate_original", flt(r.message));
						frm.set_value("advance_amount", flt(r.message) * flt(frm.doc.advance_amount_requested));
				}
			}
		});
	}
}