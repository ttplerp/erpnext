// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('Equipment', {
        refresh: function (frm) {
                cur_frm.set_df_property("engine_number", "read_only", frm.doc.engine_number ? 1 : 0)
                cur_frm.set_df_property("asset_code", "read_only", frm.doc.asset_code ? 1 : 0)
                cur_frm.set_df_property("chassis_number", "read_only", frm.doc.chassis_number ? 1 : 0)
                // cur_frm.set_df_property("hsd_type", "read_only", frm.doc.hsd_type ? 1 : 0)
                // cur_frm.set_df_property("fuelbook", "read_only", frm.doc.fuelbook ? 1 : 0) 
                cur_frm.set_df_property("equipment_category", "read_only", frm.doc.equipment_category ? 1 : 0)
        },
        validate: function (frm) {
                if (frm.doc.operators) {
                        frm.doc.operators.forEach(function (d) {
                                frm.set_value("current_operator", d.operator)
                        })
                        frm.refresh_field("current_operator")
                }
        },
        not_cdcl: function (frm) {
                cur_frm.toggle_reqd("asset_code", frm.doc.not_cdcl == 0)
                cur_frm.set_df_property("business_activity", "read_only", frm.doc.not_cdcl ? 0 : 1 )
        }
});

frappe.ui.form.on("Equipment", "refresh", function (frm) {
        cur_frm.set_query("equipment_model", function () {
                return {
                        "filters": {
                                "equipment_type": frm.doc.equipment_type
                        }
                };
        });
        cur_frm.set_query("hsd_type", function () {
                return {
                        "filters": {
                                "is_pol_item": 1,
                                // "is_hsd_item": 1,
                                "disabled": 0
                        }
                };
        });
        cur_frm.set_query("equipment_type", function () {
                return {
                        "filters": {
                                "equipment_category": frm.doc.equipment_category
                        }
                };
        });
        cur_frm.set_query("branch", function () {
                return {
                        "filters": {
                                "disabled": 0
                        }
                }
        });
        cur_frm.set_query("fuelbook", function () {
                return {
                        "filters": {
                                "is_disabled": 0,
                                "branch": frm.doc.branch
                        }
                }
        });
})

cur_frm.fields_dict['operators'].grid.get_field('operator').get_query = function (frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        if (d.employee_type == "Employee") {
                return {
                        filters: [
        			// ['Employee', 'designation', 'in', ['Operator', 'Driver']],
                                ['Employee', 'branch', '=', frm.branch],
                                ['Employee', 'status', '=', 'Active']
                        ]
                }
        }
        else {
                return {
                        filters: [
                                ['Muster Roll Employee', 'branch', '=', frm.branch],
                                ['Muster Roll Employee', 'status', '=', 'Active']
                        ]
                }
        }
}


frappe.ui.form.on('Equipment Operator', {
        employee_type: function (frm, cdt, cdn) {
                frappe.model.set_value(cdt, cdn, "operator", "");
                cur_frm.refresh_field("operator");
        },

        operator: function (frm, cdt, cdn) {
                doc = locals[cdt][cdn]
                if (doc.operator) {

                        if (doc.employee_type == "Employee") {
                                frappe.call({
                                        method: "frappe.client.get_value",
                                        args: {
                                                doctype: "Employee",
                                                fieldname: "employee_name",
                                                filters: { name: doc.operator }
                                        },
                                        callback: function (r) {
                                                if (r.message.employee_name) {
                                                        frappe.model.set_value(cdt, cdn, "operator_name", r.message.employee_name)
                                                        cur_frm.refresh_fields()
                                                }
                                        }
                                })
                        }
                        else {
                                var doc_type = "Muster Roll Employee"
                                if (doc.employee_type == "DES Employee") {
                                        doc_type = "DES Employee"
                                }
                                frappe.call({
                                        method: "frappe.client.get_value",
                                        args: {
                                                doctype: doc_type,
                                                fieldname: "person_name",
                                                filters: { name: doc.operator }
                                        },
                                        callback: function (r) {
                                                if (r.message.person_name) {
                                                        frappe.model.set_value(cdt, cdn, "operator_name", r.message.person_name)
                                                        cur_frm.refresh_fields()
                                                }
                                        }
                                })
                        }
                }
        }
})
