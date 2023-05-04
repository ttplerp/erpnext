// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Equipment Request', {
	refresh: function(frm) {
		if (frm.doc.docstatus == 1 && (!frm.doc.ehf) && (frm.doc.approval_status == 'Available' || frm.doc.approval_status == 'Partially Available')) {
			frm.add_custom_button(__("Create Equipment Hiring Form"),	() => frm.events.make_hire_form(frm), __("Create"));
			frm.page.set_inner_btn_group_as_primary(__('Create'))
		}
		frm.toggle_reqd("approval_status", frm.doc.docstatus == 1)
	},

	onload: function(frm) {
		if(frm.doc.ehf != null) {
			frm.set_df_property('approval_status', 'read_only', 1)
		}
	},

	make_hire_form: function (frm) {
        frappe.call({
            method: "make_hire_form",
            doc: frm.doc,
			callback:function(r){
				frappe.set_route('Form', r.message.doctype, r.message.name);
			}
        });
    },

	// "approval_status": function(frm, cdt, cdn) {
	// 	frm.set_indicator_formatter('equipment_type',
	// 		function(frm) {
	// 			return frm.doc.approved ? "green" : "orange"
	// 	})
	// },
	"approval_status": function(frm, cdt, cdn) {
		set_values(frm, cdt, cdn);
	}
});
	
frappe.ui.form.on('Equipment Request Item', {
	approved_qty:(frm,cdt,cdn)=>{
		check_value(frm, cdt, cdn)
	},
	from_date:(frm,cdt,cdn)=>{
		calculate_hour(frm, cdt, cdn)
	},
	to_date:(frm,cdt,cdn)=>{
		calculate_hour(frm, cdt, cdn)
	}
});
	
var calculate_hour=(frm,cdt,cdn)=>{
	var obj = locals[cdt][cdn]	
	if(obj.from_date && obj.to_date) {
		if(obj.from_date > obj.to_date) {
			msgprint("From Date Cannot Be Greater Than To Date")
			frappe.model.set_value(cdt, cdn, "to_date", "")
			frm.refresh_field('items')
		}else {
			frappe.model.set_value(cdt, cdn, "total_hours", (frappe.datetime.get_day_diff(obj.to_date, obj.from_date) + 1) * 8)
			frm.refresh_field('items')
		}
	}
}

var check_value=(frm,cdt,cdn)=>{
	va = locals[cdt][cdn]
	if(va.approved_qty > va.qty) {
		msgprint("Approved Qty Cannot Be Greater Than Requested Qty")
	} 
}
	
function set_values(frm, cdt, cdn) {
	var val = frm.doc.items || []
	var df1 = frappe.meta.get_docfield("Equipment Request Item","approved_qty", cur_frm.doc.name);
	if(frm.doc.approval_status == 'Available') {
		for( var a in val) { 
			frappe.model.set_value("Equipment Request Item", val[a].name, "approved_qty", val[a].qty)
			df1.read_only = 1
		}
	}else if (frm.doc.approval_status == 'Unavailable') {
		for (var b in val) { 
			frappe.model.set_value("Equipment Request Item", val[b].name, "approved_qty", "0.0")
			df1.read_only = 1
		}
	}else if (frm.doc.approval_status == 'Partially Available') {
		df1.read_only = 0
	}else {
		df1.read_only = 0
		msgprint("Status cannot be empty")
}}
	
	
