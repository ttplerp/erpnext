// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Job Card'] = {
    add_fields: ["payment_jv", "docstatus", "assigned_to", "outstanding_amount", "owned_by"],
    has_indicator_for_draft: 1,
    get_indicator: function (doc) {
        if (doc.docstatus == 0) {
            if (doc.assigned_to) {
                return ["Job Assigned", "orange", "docstatus,=,0|assigned_to,not like, "];
            }
            else {
                return ["Job Created", "grey", "docstatus,=,0|assigned_to,like, "];
            }
        }

        if (doc.docstatus == 1) {
            if (doc.out_source == 1) {
                // {
                // 	return ["Test", "orange", "docstatus,=,1|out_source, =,1"]
                // };
                if (doc.owned_by == "Own") {
                    return ["Own Equipment", "yellow", "docstatus,=,1|owned_by,=,Own"];
                }
                else if (doc.owned_by == "CDCL") {
                    return ["Journal Adjusted", "green", "docstatus,=,1|owned_by,=,CDCL"];
                }
                else if (doc.outstanding_amount == 0) {
                    return ["Payment Received", "green", "docstatus,=,1|outstanding_amount,=,0|owned_by,=,Others"];
                }
                else if (doc.outstanding_amount != 0 && doc.outstanding_amount < doc.total_amount) {
                    return ["Partially Received", "blue", "docstatus,=,1|outstanding_amount,!=,0|outstanding_amount,>,0|owned_by,=,Others"];
                }
                else {
                    return ["Invoice Raised", "blue", "docstatus,=,1|outstanding_amount,>,0|owned_by,=,Others"];
                }
            }
        }
    }
};
