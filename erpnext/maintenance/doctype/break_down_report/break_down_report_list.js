// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Break Down Report'] = {
	add_fields: ["docstatus", "job_card"],
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		if(doc.docstatus==0) {
			return ["Report Created", "grey", "docstatus,=,0"];
		}

		if(doc.docstatus == 1) {
			if(doc.job_card) {
				return ["Job Card Created", "green", "docstatus,=,1|job_card,>,0"];
			}
			else {
				return ["Report Completed", "blue", "docstatus,=,1|job_card,<=,0"];
			}
		}
	}
};
