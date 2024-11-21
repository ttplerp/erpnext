// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Mess Management', {
    refresh: function(frm) {
		frm.set_query("project", function(doc) {
			return {
				filters: {
					"status": "Open"
				}
			}
		});
    },
    head_count: function(frm) {
        calculate_amount(frm);
    },
    rate_per_head: function(frm) {
        calculate_amount(frm);
    }
});

function calculate_amount(frm) {
    var amount = 0.00;
    if (frm.doc.head_count && frm.doc.rate_per_head) {
        amount = parseFloat(frm.doc.head_count) * parseFloat(frm.doc.rate_per_head);
    }
    frm.set_value("amount", amount);
    frm.refresh_field("amount");
}

