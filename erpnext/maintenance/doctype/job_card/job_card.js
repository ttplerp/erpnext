// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on("Job Card", {
	setup: function (frm) {
		frm.get_field("assigned_to").grid.editable_fields = [
			{ fieldname: "mechanic", columns: 3 },
			{ fieldname: "start_time", columns: 3 },
			{ fieldname: "end_time", columns: 3 },
			{ fieldname: "total_time", columns: 1 },
		];
	},
	refresh: function (frm) {
		if (frm.doc.docstatus === 1) {
			frappe.call({
				method: "erpnext.maintenance.doctype.job_card.job_card.get_payment_entry",
				args: {
					doc_name: frm.doc.name,
					total_amount: frm.doc.total_amount
				},
				callback: function (r) {
					cur_frm.refresh_field("payment_status");
				},
			})

			if(!frm.doc.settled_using_imprest){
				frm.add_custom_button(
					__("Accounting Ledger"),
					function () {
						frappe.route_options = {
							voucher_no: frm.doc.name,
							from_date: frm.doc.finish_date,
							to_date: frm.doc.finish_date,
							company: frm.doc.company,
							group_by_voucher: false,
						};
						frappe.set_route("query-report", "General Ledger");
					},
					__("View")
				);
			}
			
			frm.add_custom_button(
				__("Journal Entry"),
				function () {
					frappe.route_options = {
					name: frm.doc.journal_entry
					};
					frappe.set_route("List", "Journal Entry");
				},
				__("View")
			);

			if (frm.doc.out_source == 1 && frm.doc.docstatus == 1 && !frm.doc.settled_using_imprest && !frm.doc.journal_entry) {
				frm.add_custom_button(
					__("Make Payment"),
					function () {
						frappe.call({
							method: "make_journal_entry",
							doc: frm.doc,
							callback: function(r){
								frm.refresh();
							}
						});	
					},
					__("Make Payment")
				);
			}
		}
		
		// if (frappe.model.can_read("Journal Entry")) {
		// 	cur_frm.add_custom_button(
		// 		__("Bank Entries"),
		// 		function () {
		// 			frappe.route_options = {
		// 				"Journal Entry Account.reference_type": me.frm.doc.doctype,
		// 				"Journal Entry Account.reference_name": me.frm.doc.name,
		// 			};
		// 			frappe.set_route("List", "Journal Entry");
		// 		},
		// 		__("View")
		// 	);
		// }

		cur_frm.toggle_display("owned_by", 0);
	},

	items_on_form_rendered: function (frm, grid_row, cdt, cdn) {
		var row = cur_frm.open_grid_row();
		var df = frappe.meta.get_docfield("Job Card Item", "quantity", cur_frm.doc.name);
		if (!row.grid_form.fields_dict.stock_entry.value) {
			df.read_only = 0;
			row.grid_form.fields_dict.quantity.refresh();
		} else {
			df.read_only = 1;
			row.grid_form.fields_dict.quantity.refresh();
		}
	},

	settled_using_imprest: function(frm) {
		frm.toggle_reqd(["expense_account"], (frm.doc.settled_using_imprest ? 1 : 0));
	},

	tax_withholding_category: function(frm) {
		frappe.call({
			method: "get_tax_details",
			doc: frm.doc,
			callback: function(r) {
				console.log(r.message.account);
				frm.set_value("tds_account", r.message.account);
				frm.set_value("tds_amount", flt(cur_frm.doc.total_amount * flt(r.message.rate / 100)));
				frm.set_value("net_amount", cur_frm.doc.total_amount - flt(cur_frm.doc.total_amount * flt(r.message.rate / 100)));
				frm.refresh();
			}
		});
	}
});

frappe.ui.form.on("Job Card Item", {
	job: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn];
		var vendor = frm.doc.supplier;
		var fiscal_year = frm.doc.posting_date; 
		if (item.job) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: item.which,
					fieldname: ["item_name", "cost"],
					filters: {
						name: item.job,
					},
				},
				callback: function (r) {
					frappe.model.set_value(cdt, cdn, "job_name", r.message.item_name);
					var charge_amount = item.quantity * r.message.cost;
					frappe.model.set_value(cdt, cdn, "amount", r.message.cost);
					frappe.model.set_value(cdt, cdn, "charge_amount", charge_amount);
					cur_frm.refresh_field("job_name");
					cur_frm.refresh_field("amount");
					cur_frm.refresh_field("charge_amount")
				},
			});

		}
	},
	
	quantity: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn];
		update_rate_quantity_amount(item, frm, cdt, cdn)
	},
	amount: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn];
		update_rate_quantity_amount(item, frm, cdt, cdn)
	},
});

function update_rate_quantity_amount(item, frm, cdt, cdn) {
	var charge_amount = item.quantity * item.amount;
	frappe.model.set_value(cdt, cdn, "charge_amount", charge_amount);
	cur_frm.refresh_field("charge_amount")
}

frappe.ui.form.on("Mechanic Assigned", {
	start_time: function (frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn);
	},
	end_time: function (frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn);
	},
	mechanic: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn];
		if (item.employee_type == "Employee") {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					fieldname: "employee_name",
					filters: { name: item.mechanic },
				},
				callback: function (r) {
					if (r.message.employee_name) {
						frappe.model.set_value(cdt, cdn, "employee_name", r.message.employee_name);
						cur_frm.refresh_fields();
					}
				},
			});
		} else {
			var doc_type = "Muster Roll Employee";
			if (item.employee_type == "DES Employee") {
				doc_type = "DES Employee";
			}
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: doc_type,
					fieldname: "person_name",
					filters: { name: item.mechanic },
				},
				callback: function (r) {
					if (r.message.person_name) {
						frappe.model.set_value(cdt, cdn, "employee_name", r.message.person_name);
						cur_frm.refresh_fields();
					}
				},
			});
		}
	},
});

function calculate_time(frm, cdt, cdn) {
	var item = locals[cdt][cdn];
	if (item.start_time && item.end_time && item.end_time >= item.start_time) {
		frappe.model.set_value(cdt, cdn, "total_time", frappe.datetime.get_hour_diff(item.end_time, item.start_time));
	}
	cur_frm.refresh_field("total_time");
}

cur_frm.fields_dict["assigned_to"].grid.get_field("mechanic").get_query = function (frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	if (d.employee_type == "Employee") {
		return {
			filters: [
				["Employee", "is_job_card_employee", "=", 1],
				["Employee", "status", "=", "Active"],
			],
		};
	} else if (d.employee_type == "DES Employee") {
		return {
			filters: [
				["DES Employee", "list_in_job_card", "=", 1],
				["DES Employee", "status", "=", "Active"],
			],
		};
	} else {
		return {
			filters: [
				["Muster Roll Employee", "list_in_job_card", "=", 1],
				["Muster Roll Employee", "status", "=", "Active"],
			],
		};
	}
};