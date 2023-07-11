// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'branch', 'branch');
frappe.ui.form.on('Vehicle Request', {
    refresh: function (frm) {
        if(frm.doc.workflow_state == "Waiting MTO Approval" || frm.doc.workflow_state == "Waiting DG Approval"){
            cur_frm.toggle_display("section_break_003", frappe.user.has_role(["ADM User","CEO"]));
        }else if(frm.doc.workflow_state == "Approved"){
            cur_frm.toggle_display("section_break_003", 1);
        }else{
            cur_frm.toggle_display("section_break_003", 0);
        }
    },
    setup: function (frm) {
        frm.get_field('items').grid.editable_fields = [
            { fieldname: 'employee', columns: 2 },
            { fieldname: 'employee_name', columns: 2 },
            { fieldname: 'designation', columns: 2 },
            { fieldname: 'division', columns: 3 },
        ];
    },
})

//Returns own equipments
cur_frm.fields_dict.equipment.get_query = function (doc) {}

//Returns list of Active Employee
/*cur_frm.fields_dict['items'].grid.get_field('employee').get_query = function(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        return {
            query: "erpnext.controllers.queries.employee_query",
            filters: {'branch': frm.branch}
        }
}*/
