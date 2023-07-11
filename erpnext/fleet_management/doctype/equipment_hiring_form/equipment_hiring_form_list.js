// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
/*frappe.listview_settings['Equipment Hiring Form'] = {
	add_fields: ["hiring_status", "docstatus", "payment_completed"],
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		if(doc.docstatus==0) {
				return ["Hiring Requested", "grey", "docstatus,=,0"];
		}

		if(doc.docstatus == 1) {
			if(!doc.hiring_status && !doc.payment_completed) {
				return ["Hiring Approved", "blue", "docstatus,=,1"];
			}
			else if(doc.hiring_status && !doc.payment_completed) {
				return ["Logbook Submitted", "orange", "docstatus,=,1|hiring_status,>,0|payment_completed,=,0"];
			}
			else if(doc.payment_completed) {
				return ["Closed", "green", "docstatus,=,1|payment_completed,>,0"];
			}
			else {
			}
		}
		
		if(doc.docstatus == 2) {
			return ["Cancelled", "red", "docstatus,=,2"]
		}
	}
};*/
