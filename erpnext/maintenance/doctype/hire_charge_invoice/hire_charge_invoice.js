// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hire Charge Invoice', {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1) {
			// frappe.call({
			// 	method: "erpnext.maintenance.doctype.hire_charge_invoice.hire_charge_invoice.get_payment_entry",
			// 	args: {
			// 	  doc_name: frm.doc.name,
			// 	  total_amount: frm.doc.balance_amount
			// 	},
			// 	callback: function (r) {
			// 	  cur_frm.refresh_field("payment_status");
			// 	},
			//   })
			frm.add_custom_button(__('Accounting Ledger'), function () {
				frappe.route_options = {
					voucher_no: frm.doc.name,
					from_date: frm.doc.posting_date,
					to_date: frm.doc.posting_date,
					company: frm.doc.company,
					group_by_voucher: false
				};
				frappe.set_route("query-report", "General Ledger");
			}, __("View"));
		}

		if (frm.doc.invoice_jv && frappe.model.can_read("Journal Entry")) {
			cur_frm.add_custom_button(__('Bank Entries'), function () {
				frappe.route_options = {
					"Journal Entry Account.reference_type": me.frm.doc.doctype,
					"Journal Entry Account.reference_name": me.frm.doc.name,
				};
				frappe.set_route("List", "Journal Entry");
			}, __("View"));
		}
		if (frm.doc.owned_by != "Own Company" && frm.doc.outstanding_amount > 0 && frappe.model.can_write("Journal Entry") && frm.doc.docstatus == 1) {
			/*//cur_frm.toggle_display("receive_payment", 1)
			cur_frm.add_custom_button(__('Payment'), function() {
				cur_frm.cscript.receive_payment()
			}, __("Receive")); */
			frm.add_custom_button("Make Payment", function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.maintenance.doctype.hire_charge_invoice.hire_charge_invoice.make_payment_entry",
					frm: cur_frm
				})
			}, __("Payment"));
		}
		else {
			cur_frm.toggle_display("make_payment", 0)
		}
	},
	onload: function (frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today());
		}
		if (frm.doc.branch){
			frappe.call({
				'method': "frappe.client.get",
				'args': {
					'doctype': "Branch",
					'filters': {
						"name": frm.doc.branch
					},
					'fields': ["cost_center"]				
				},
				callback: function(r){
					cur_frm.set_value("cost_center", r.message.cost_center);
					cur_frm.refresh_field("cost_center")
				}
			});
		}
	},
	ehf_name: function(frm){
		if (frm.doc.ehf_name){
			frappe.call({
				'method': "frappe.client.get",
				'args': {
					'doctype': "Equipment Hiring Form",
					'filters': {
						"name": frm.doc.ehf_name
					},
					'fields': ["supplier"]				
				},
				callback: function(r){
					cur_frm.set_value("customer", r.message.supplier);
					cur_frm.refresh_field("customer")
				}
			});
		}
	},
	tax_withholding_category: function(frm) {
		frappe.call({
			method: "get_tax_details",
			doc: frm.doc,
			callback: function(r) {
				console.log(r.message.account);
				frm.set_value("tds_account", r.message.account);
				frm.set_value("tds_amount", flt(cur_frm.doc.total_invoice_amount * flt(r.message.rate / 100)));
				frm.refresh();
				calculate_balance(frm)
			}
		});
	},
	// "tds_percentage": function (frm) {
	// 	if (frm.doc.tds_percentage != "") {
	// 		frm.set_value("tds_amount", frm.doc.tds_percentage / 100 * frm.doc.total_invoice_amount)
	// 		cur_frm.refresh_field("tds_amount")
	// 		calculate_balance(frm)
	// 	}
	// 	else {
	// 		cur_frm.refresh_field("tds_amount")
	// 		calculate_balance(frm)
	// 	}
	// },
	"get_vehicle_logbooks": function (frm) {
		get_vehicle_logs(frm.doc.ehf_name, frm.doc.branch)
	},
	"advance_amount": function (frm) {
		calculate_balance(frm)
	},
	"total_invoice_amount": function (frm) {
		calculate_balance(frm)
	},
	"discount_amount": function (frm) {
		calculate_balance(frm)
	},
	"get_advances": function (frm) {
		get_advances(frm.doc.ehf_name)
	},
	"receive_payment": function (frm) {
		if (!frm.doc.payment_jv) {
			return frappe.call({
				method: "erpnext.maintenance.doctype.hire_charge_invoice.hire_charge_invoice.make_bank_entry",
				args: {
					"frm": cur_frm.doc.name,
				},
				callback: function (r) {
					cur_frm.refresh()
				}
			});
		}
		cur_frm.refresh_field("payment_jv")
		cur_frm.refresh_field("receive_payment")
		cur_frm.refresh()
	}
});


function calculate_balance(frm) {
	if (frm.doc.total_invoice_amount) {
		if (!frm.doc.advance_amount) { frm.doc.advance_amount = 0 }
		if (!frm.doc.discount_amount) { frm.doc.discount_amount = 0 }
		if (!frm.doc.tds_amount) { frm.doc.tds_amount = 0 }
		frm.set_value("balance_amount", frm.doc.total_invoice_amount - frm.doc.advance_amount - frm.doc.discount_amount - frm.doc.tds_amount)
		frm.refresh_field("balance_amount")
		frm.set_value("outstanding_amount", frm.doc.balance_amount)
		frm.refresh_field("outstanding_amount")
	}
}

// cur_frm.add_fetch("ehf_name", "customer", "customer")
// cur_frm.add_fetch("ehf_name", "private", "owned_by")
// cur_frm.add_fetch("branch", "cost_center", "cost_center")
//cur_frm.add_fetch("ehf_name","advance_amount","advance_amount")


// frappe.ui.form.on("Hire Charge Invoice", "refresh", function(frm) {
//     cur_frm.set_query("ehf_name", function() {
//         return {
//             "filters": {
//                 "payment_completed": 0,
// 		"docstatus": 1,
// 		"branch": frm.doc.branch
//             }
//         };
//     });
// })

frappe.ui.form.on('Hire Invoice Details', {
	"discount_amount": function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		if (item.discount_amount >= 0 && item.discount_amount <= item.total_amount) {
			calculate_discount_total(frm)
		}
		else {
			frappe.msgprint("Discount Amount should be between 0 and Total amount")
			frm.set_value("discount_amount", 0)
			frm.refresh_field("discount_amount")
		}
	}
})

frappe.ui.form.on('Hire Invoice Advance', {
	"allocated_amount": function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		if (item.allocated_amount >= 0 && item.allocated_amount <= item.actual_advance_amount) {
			calculate_advance_total(frm)
		}
		else {
			frappe.msgprint("Allocated Amount should be between 0 and advance amount")
			frm.set_value("allocated_amount", item.actual_advance_amount)
			frm.refresh_field("allocated_amount")
		}
	}
})

function calculate_advance_total(frm) {
	var total = 0;
	var bal_total = 0;
	frm.doc.advances.forEach(function (d) {
		total += d.allocated_amount
		bal_total += d.balance_advance_amount
	})
	frm.set_value("advance_amount", total)
	frm.set_value("balance_advance_amount", bal_total)
	frm.refresh_field("advance_amount")
	frm.refresh_field("balance_advance_amount")
}

function calculate_discount_total(frm) {
	var total = 0;
	frm.doc.items.forEach(function (d) {
		total += d.discount_amount
	})
	frm.set_value("discount_amount", total)
	frm.refresh_field("discount_amount")
}

function get_vehicle_logs(form, branch) {
	frappe.call({
		method: "erpnext.maintenance.doctype.hire_charge_invoice.hire_charge_invoice.get_vehicle_logs",
		async: false,
		args: {
			"form": form,
			"branch": branch,
		},
		callback: function (r) {
			console.log(r.message)
			if (r.message) {
				var total_invoice_amount = 0;
				cur_frm.clear_table("items");
				r.message.forEach(function (logbook) {
					var row = frappe.model.add_child(cur_frm.doc, "Hire Invoice Details", "items");
					row.vehicle_logbook = logbook['name']
					row.equipment_number = logbook['equipment_number']
					row.equipment = logbook['equipment']
					row.rate_type = logbook['rate_type']
					row.number_of_days = logbook['total_days']
					row.total_km = logbook['total_km']
					row.hiring_rate = logbook['rate']
					row.total_amount = logbook['total_amount']
					refresh_field("items");

					total_invoice_amount += row.total_amount
					// COMMENTED BY PHUNTSHO ON MARCH 11 2021! NOT NEEDED FOR DESUUNG. 
					// frappe.call({
					// 	method: "erpnext.maintenance.doctype.hire_charge_invoice.hire_charge_invoice.get_vehicle_accessories",
					// 	async: false,
					// 	args: {
					// 		"form": form,
					// 		"equipment": logbook['equipment']
					// 	},
					// 	callback: function(r) {
					// 		if(r.message) {
					// 			r.message.forEach(function(access) {
					// 				var row = frappe.model.add_child(cur_frm.doc, "Hire Invoice Details", "items");
					// 				row.vehicle_logbook = logbook['name']
					// 				row.equipment_number = access['name']
					// 				row.equipment = logbook['equipment']
					// 				row.rate_type = logbook['rate_type']
					// 				row.total_work_hours = logbook['total_work_time']
					// 				row.total_idle_hours = logbook['total_idle_time']
					// 				row.work_rate = access['work']
					// 				row.idle_rate = access['idle']
					// 				row.amount_idle = logbook['total_idle_time'] * access['idle']
					// 				row.amount_work = logbook['total_work_time'] * access['work']
					// 				row.number_of_days = logbook['no_of_days']
					// 				row.total_amount = (row.amount_idle + row.amount_work)
					// 				refresh_field("items");

					// 				total_invoice_amount += (row.amount_idle + row.amount_work)
					// 			})
					// 		}
					// 	},
					// 	freeze: true,
					// 	freeze_message: "Getting Logbook Details.... Please Wait"
					// });
				});

				cur_frm.set_value("total_invoice_amount", total_invoice_amount)
				cur_frm.refresh_field("total_invoice_amount")
				cur_frm.refresh()
			}
			else {
				frappe.msgprint("No Vehicle Logs found!")
			}
		}
	})
}

//Get Advance Details
function get_advances(hire_name) {
	frappe.call({
		method: "erpnext.maintenance.doctype.hire_charge_invoice.hire_charge_invoice.get_advances",
		args: {
			"hire_name": hire_name,
		},
		callback: function (r) {
			if (r.message) {
				var total_advance_amount = 0;
				cur_frm.clear_table("advances");
				r.message.forEach(function (adv) {
					var row = frappe.model.add_child(cur_frm.doc, "Hire Invoice Advance", "advances");
					row.jv_name = adv['name']
					row.reference_row = adv['reference_row']
					row.actual_advance_amount = adv['amount']
					row.allocated_amount = adv['amount']
					row.advance_account = adv['advance_account']
					row.advance_cost_center = adv['cost_center']
					row.remarks = adv['remark']
					refresh_field("advances");

					total_advance_amount += row.allocated_amount
				});

				cur_frm.set_value("advance_amount", total_advance_amount)
				cur_frm.refresh()
			}
			else {
				frappe.msgprint("No Advances found!")
			}
		}
	})
}

cur_frm.cscript.receive_payment = function () {
	var doc = cur_frm.doc;
	frappe.ui.form.is_saving = true;
	frappe.call({
		method: "erpnext.maintenance.doctype.hire_charge_invoice.hire_charge_invoice.make_bank_entry",
		args: {
			"frm": cur_frm.doc.name,
		},
		callback: function (r) {
			cur_frm.reload_doc();
		},
		always: function () {
			frappe.ui.form.is_saving = false;
		}
	});
}
