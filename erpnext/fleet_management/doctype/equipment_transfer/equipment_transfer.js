// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Equipment Transfer', {
    onload: function (frm) {
        let grid = frm.fields_dict['items'].grid;
        grid.cannot_add_rows = true; // Disable adding new rows in the grid
    },

    refresh: function (frm) {
        if (frm.doc.docstatus !== 1 && !frm.is_new()) {
            frm.add_custom_button(__("Get Equipment"), function () {
                frm.events.get_equipment_details(frm);
            }).toggleClass("btn-primary", !(frm.doc.items || []).length);
        }
    },

    get_equipment_details: function (frm) {
        frappe.call({
            doc: frm.doc,
            method: "fill_equipment_details",
            freeze: true,
            freeze_message: __("Fetching Equipment"),
        }).then((r) => {
            if (r.docs?.[0]?.items) {
                frm.dirty();
                frm.save();
            }
            frm.refresh();
            frm.scroll_to_field("items");
        }).catch((err) => {
            frappe.msgprint(__('Failed to fetch equipment details.'));
            console.error(err);
        });
    },

	to_branch: function (frm) {
		frm.events.set_branch_in_children(frm, frm.doc.items, "to_branch", frm.doc.to_branch);
		frm.events.set_cost_center_in_children(frm, frm.doc.items, "to_cost_center", frm.doc.to_cost_center);
	},
	
	set_branch_in_children: function (frm, child_table, branch_field, to_branch) {
		if (!child_table || !child_table.length) {
			console.warn("No child table data found.");
			return;
		}
	
		frm.events.autofill_field(child_table, branch_field, to_branch);
	},
	
	set_cost_center_in_children: function (frm, child_table, cost_center_field, to_cost_center) {
		if (!child_table || !child_table.length) {
			console.warn("No child table data found.");
			return;
		}
	
		frm.events.autofill_field(child_table, cost_center_field, to_cost_center);
	},
	
	autofill_field: function (child_table, field_name, field_value) {
		const doctype = child_table[0].doctype;
	
		child_table.forEach((item) => {
			frappe.model.set_value(doctype, item.name, field_name, field_value);
		});
	}
});

