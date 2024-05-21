// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Break Down Report', {
	refresh: function(frm) {
		if( frm.doc.docstatus === 1){
			frappe.call({
				method: "erpnext.maintenance.doctype.break_down_report.break_down_report.get_job_card_entry",
				args: {
					doc_name: frm.doc.name
				},
				callback: function (r) {
					cur_frm.refresh_field("job_card_status");
				},
			})
		}

		if (frm.doc.docstatus == 1 && !frm.doc.job_card) {
			frm.add_custom_button("Create Job Card", function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.maintenance.doctype.break_down_report.break_down_report.make_job_card",
					frm: cur_frm
				})
			});
		}

	},
	onload: function(frm) {
		if (!frm.doc.date) {
			frm.set_value("date", get_today());
		}
			
		// Ver 2.0 Begins, following code added by SHIV on 28/11/2017
		if(frm.doc.__islocal) {
			frappe.call({
				method: "erpnext.custom_utils.get_user_info",
				args: {"user": frappe.session.user},
				callback(r) {
					cur_frm.set_value("cost_center", r.message.cost_center);
					cur_frm.set_value("branch", r.message.branch);
					cur_frm.set_value("company", r.message.company);
				}
			});
		}
	},
		
	owned_by: function(frm) {
		cur_frm.set_value("customer", "")
		cur_frm.set_value("equipment", "")
	}
		
});

cur_frm.add_fetch("customer", "customer_group", "client");

frappe.ui.form.on("Break Down Report", "refresh", function(frm) {
    cur_frm.set_query("equipment", function() {
		if (frm.doc.owned_by == "Own Branch") {
			return {
				"filters": {
					"is_disabled": 0,
					"branch": frm.doc.branch
				}
			};
		}
    });

    cur_frm.set_query("cost_center", function() {
        return {
            "filters": {
				"is_group": 0,
				"is_disabled": 0
            }
        };
    });

    cur_frm.set_query("customer", function() {
		if(frm.doc.owned_by == "Own Branch") {
			return {
				"filters": {
					"disabled": 0,
					"cost_center": frm.doc.cost_center,
					"branch": frm.doc.branch
				}
			};
		}
    });
});

frappe.ui.form.on('Job Card Item', {
	job: (frm, cdt, cdn) => {
		var items = locals[cdt][cdn];
		if (items.job) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: items.which,
					fieldname: ["item_name"],
					filters: {
						name: items.job
					},
				},
				callback: function (r) {
					frappe.model.set_value(cdt, cdn, "job_name", r.message.item_name);
					cur_frm.refresh_field("job_name");
				}
			})
			if (frm.doc.equipment){
				frappe.call({
					method:'erpnext.maintenance.doctype.break_down_report.break_down_report.fetch_previous_date',
					args:{
						equipment:frm.doc.equipment,
						item_code:items.job
					},
					callback:function(r){
						if(r.message.length){
							frappe.model.set_value(cdt, cdn, "recent_maintenance_date", r.message[0].recent_maintenance_date);
							frappe.model.set_value(cdt, cdn, "recent_km", r.message[0].current_km);
							frappe.model.set_value(cdt, cdn, "km_difference", parseFloat(frm.doc.current_km) - parseFloat(r.message[0].current_km));
						}else{
							frappe.model.set_value(cdt, cdn, "recent_maintenance_date", frm.doc.date);
							frappe.model.set_value(cdt, cdn, "recent_km", frm.doc.current_km);
							frappe.model.set_value(cdt, cdn, "km_difference", frm.doc.current_km);
						}
					}
				})
			}
		}
	},
	quantity: (frm,cdt,cdn)=>{
		calculate_amount(frm,cdt,cdn)
	},
	amount: (frm,cdt,cdn)=>{
		calculate_amount(frm,cdt,cdn)
	}
})

var calculate_amount = (frm,cdt,cdn)=>{
	var item = locals[cdt][cdn]
	if (item.quantity && item.amount){
		item.charge_amount = item.quantity * item.amount 
		cur_frm.refresh_field('items')
	}
}
