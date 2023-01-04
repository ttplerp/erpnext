// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['POL'] = {
	add_fields: ["docstatus", "outstanding_amount", "paid_amount"],
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		if(doc.docstatus==0) {
			return ["Receive POL Created", "darkgrey", "docstatus,=,0"];
		}

		if(doc.docstatus == 1) {
			if(doc.outstanding_amount > 0 && doc.paid_amount > 0) {
				return ["Partially Paid", "blue", "docstatus,=,1|outstanding_amount,>,0|paid_amount,>,0"];
			}
			else if(doc.outstanding_amount > 0 && doc.paid_amount == 0) {
				return ["Unpaid", "orange", "docstatus,=,1|outstanding_amount,>,0|paid_amount,=,0"];
			}
			else if(doc.outstanding_amount == 0) {
				return ["Paid", "green", "docstatus,=,1|outstanding_amount,=,0"];
			}
			else {
			}
		}
	}
};
