// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Advance Settlement', {
	refresh: function(frm) {
		refresh_html(frm);
	},

	advance_type: function(frm) {
		reset_values(frm);
		if (frm.doc.advance_type) {
            return frappe.call({
                method: 'erpnext.accounts.doctype.supplier_advance_settlement.supplier_advance_settlement.get_balance_amount',
                args: {
                    supplier: frm.doc.supplier,
                    advance_type: frm.doc.advance_type
                },
                callback: function(r) {
                    let docs = r.message;
                    set_form_data(docs, frm);
				    refresh_fields(frm);
                }
            })
            
        }
	}

});

function set_form_data(data, frm) {	
	frm.doc.balance_amount = flt(data);
}

function reset_values(frm) {
	frm.set_value("balance_amount", 0);
}

function refresh_fields(frm) {
	frm.refresh_field("balance_amount");
}

var refresh_html = function(frm){
	var journal_entry_status = "";
	if(frm.doc.journal_entry_status){
		journal_entry_status = '<div style="font-style: italic; font-size: 0.8em; ">* '+frm.doc.journal_entry_status+'</div>';
	}
	
	if(frm.doc.journal_entry){
		$(cur_frm.fields_dict.journal_entry_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Journal Entry</label><br><b>'+'<a href="/desk/Form/Journal Entry/'+frm.doc.journal_entry+'">'+frm.doc.journal_entry+"</a> "+"</b>"+journal_entry_status);
	}	
}
