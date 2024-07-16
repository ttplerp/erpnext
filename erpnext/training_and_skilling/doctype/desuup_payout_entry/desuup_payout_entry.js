// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
{% include "erpnext/public/js/controllers/cheque_details.js" %};

frappe.ui.form.on('Desuup Payout Entry', {
	onload: function (frm) {
		frm.set_query('training_management', function(doc) {
			return {
				filters: {
					"status": "On Going",
					"training_center": doc.training_center,

				}
			};
		});
		frm.set_query('desuup_deployment', function(doc) {
			return {
				filters: {
					"status": "On Going",
				}
			};
		});
		frm.set_query('branch', function(doc) {
			return {
				filters: {
					"company": frm.doc.company,
				}
			};
		});

		create_custom_buttons(frm);
	},
	refresh: function(frm) {
		create_custom_buttons(frm);
	},

	get_desuups: function (frm) {
		frm.set_value("number_of_desuups", 0);
		frm.refresh_field("number_of_desuups");
		return frappe.call({
			doc: frm.doc,
			method: 'get_desuup_details',
			callback: function(r) {
				if (r.message){
					frm.set_value("number_of_desuups", r.message);
					frm.refresh_field("number_of_desuups");
					frm.refresh_field("items");
					frm.dirty();
				}
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching Desuup Records...</span>'
		});
	},

	fiscal_year: function (frm) {
		frm.events.clear_items_table(frm);
	},

	month_name: function (frm) {
		frm.events.clear_items_table(frm);
		frm.call({
			doc: frm.doc,
			method: "set_month_dates",
			callback: function(r) {
				frm.refresh_field("start_date");
				frm.refresh_field("end_date");
			},
		})
	},

	clear_items_table: function (frm) {
		frm.clear_table('items');
		frm.refresh();
	},
});

frappe.ui.form.on('Desuup Payout Item', {
    refresh: function(frm) {
        calculate_row_total(frm);
    },
    // Trigger calculations when the row is added
    items_add: function(frm) {
        calculate_row_total(frm);
    },
    // Recalculate totals when a row is removed from the items table
    items_remove: function(frm) {
        calculate_row_total(frm);
    },
    // Recalculate totals when a row field is changed
    items_on_form_rendered: function(frm) {
        calculate_row_total(frm);
    }
});

function calculate_row_total(frm) {
    let total_items_count = frm.doc.items ? frm.doc.items.length : 0;
    console.log(`Total items count: ${total_items_count}`);

    // Update the total_items_count field on the form
    frm.set_value('number_of_desuups', total_items_count);
    frm.refresh_field('number_of_desuups');
}


/* ePayment Begins */
var create_custom_buttons = function(frm){
	var status = ["Failed", "Upload Failed", "Cancelled", "Payment Failed", "Payment Cancelled"];

	if(frm.doc.docstatus == 1 && frm.doc.payment_status != "Payment Successful"){
		if(!frm.doc.bank_payment || status.includes(frm.doc.payment_status) ){
			frm.page.set_primary_action(__('Process Payment'), () => {
				frappe.model.open_mapped_doc({
					method: "erpnext.training_and_skilling.doctype.desuup_payout_entry.desuup_payout_entry.make_bank_payment",
					frm: cur_frm
				})
			});
		}
	}
}
/* ePayment Ends */
