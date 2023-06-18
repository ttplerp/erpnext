// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Technical Sanction Advance', {
	onload: function (frm) {
		if (frm.doc.__islocal && frm.doc.project) {
			set_defaults(frm.doc);
		}
	},
	refresh: function(frm) {
		refresh_html(frm);
		if (frm.doc.journal_entry) {
			frm.add_custom_button(__('Bank Entries'), function () {
				frappe.route_options = { "name": frm.doc.journal_entry };
				frappe.set_route("List", "Journal Entry");
			}, __("View"));
		}
	},
	"advance_amount_requested": function (frm) {
		frm.doc.advance_amount = frm.doc.advance_amount_requested
	},
});

var refresh_html = function (frm) {
	var journal_entry_status = "";
	if (frm.doc.journal_entry_status) {
		journal_entry_status = '<div style="font-style: italic; font-size: 0.8em; ">* ' + frm.doc.journal_entry_status + '</div>';
	}

	if (frm.doc.journal_entry) {
		$(cur_frm.fields_dict.journal_entry_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Journal Entry</label><br><b>' + '<a href="/desk#Form/Journal Entry/' + frm.doc.journal_entry + '">' + frm.doc.journal_entry + "</a> " + "</b>" + journal_entry_status);
	}
}

var set_defaults = function (doc) {
	cur_frm.call({
		method: "set_defaults",
		doc: doc
	});
}