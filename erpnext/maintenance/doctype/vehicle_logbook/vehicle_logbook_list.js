// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Vehicle Logbook'] = {
	add_fields: ["invoice_created", "docstatus", "payment_completed"],
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		if(doc.docstatus==0) {
				return ["Logbook Created", "grey", "docstatus,=,0"];
		}

		if(doc.docstatus == 1) {
			if(doc.invoice_created) {
				return ["Invoice Created", "blue", "docstatus,=,1|invoice_created,>,0"];
			}
			else if(doc.invoice_created && doc.payment_completed) {
				return ["Payment Completed", "green", "docstatus,=,1|invoice_created,>,0|payment_completed,>,0"];
			}
			else {
				return ["Logbook Submitted", "orange", "docstatus,=,1|invoice_created,<,0|payment_completed,<,0"];
			}
		}
		
		if(doc.docstatus == 2) {
			return ["Logbook Cancelled", "red", "docstatus,=,2"]
		}
	}
};
