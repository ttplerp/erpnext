// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('MR TDS Receipt Update', {
	onload: function (frm) {
		let grid = frm.fields_dict['employees'].grid;
		grid.cannot_add_rows = true;
	},

	refresh: function (frm) {
		// =========================================================
		// GET MR EMPLOYEES BUTTON
		// =========================================================
		if (frm.doc.purpose == "Employee Salary") {
			frm.add_custom_button(__("Get MR Employees"), function () {
				frm.events.get_employee_details(frm);
			}).toggleClass("btn-primary", !(frm.doc.employees || []).length);
		}

		// =========================================================
		// GET INVOICES BUTTON
		// =========================================================
		if (frm.doc.docstatus == 0 && in_list(["Other Invoice", "Leave Encashment", "Overtime"], frm.doc.purpose)) {
			frm.add_custom_button(__('Get Invoices'), (doc) => {
				get_invoices(frm);
			}).addClass("btn-primary")
		}

		// =========================================================
		// JOURNAL ENTRY BUTTONS (only for submitted docs)
		// =========================================================
		if (frm.doc.docstatus == 1) {
			// --- Create Journal Entry (Draft) ---
			// Show only if no JE exists yet
			if (!frm.doc.journal_entry) {
				frm.add_custom_button(__('Create Journal Entry'), function () {
					frappe.confirm(
						__('Are you sure you want to create a Journal Entry in <b>Draft</b> status?'),
						function () {
							frappe.call({
								doc: frm.doc,
								method: 'post_journal_entry',
								freeze: true,
								freeze_message: __('Creating Journal Entry...'),
								callback: function (r) {
									if (!r.exc) {
										frm.reload_doc();
									}
								}
							});
						}
					);
				}, __('Journal Entry'));

				// --- Create & Submit Journal Entry ---
				frm.add_custom_button(__('Create & Submit Journal Entry'), function () {
					frappe.confirm(
						__('Are you sure you want to create AND submit the Journal Entry? This action cannot be undone.'),
						function () {
							frappe.call({
								doc: frm.doc,
								method: 'create_and_submit_journal_entry',
								freeze: true,
								freeze_message: __('Creating and submitting Journal Entry...'),
								callback: function (r) {
									if (!r.exc) {
										frm.reload_doc();
									}
								}
							});
						}
					);
				}, __('Journal Entry'));
			}

			// --- Submit Journal Entry (Draft → Submitted) ---
			if (frm.doc.journal_entry && frm.doc.journal_entry_status === "Draft") {
				frm.add_custom_button(__('Submit Journal Entry'), function () {
					frappe.confirm(
						__('Are you sure you want to submit the Journal Entry <b>{0}</b>?', [frm.doc.journal_entry]),
						function () {
							frappe.call({
								doc: frm.doc,
								method: 'submit_journal_entry',
								freeze: true,
								freeze_message: __('Submitting Journal Entry...'),
								callback: function (r) {
									if (!r.exc) {
										frm.reload_doc();
									}
								}
							});
						}
					);
				}, __('Journal Entry'));
			}

			// --- View Journal Entry (always show if JE exists) ---
			if (frm.doc.journal_entry) {
				frm.add_custom_button(__('View Journal Entry'), function () {
					frappe.set_route('Form', 'Journal Entry', frm.doc.journal_entry);
				}, __('Journal Entry'));
			}
		}

		// =========================================================
		// QUERIES
		// =========================================================
		frm.set_query("bulk_leave_encashment", function (frm) {
			return {
				filters: {
					docstatus: 1,
					tds_receipt_number: ["in", [null, ""]]
				}
			};
		});

		frm.set_query("pbva", function () {
			return {
				query: "erpnext.accounts.doctype.tds_receipt_update.tds_receipt_update.apply_pbva_filter",
			};
		});

		// =========================================================
		// DASHBOARD INDICATORS
		// =========================================================
		// Show status message for MR employees
		if (frm.doc.purpose == "Employee Salary" && frm.doc.docstatus == 0) {
			frm.dashboard.set_headline(__("Fetching MR employees from MR Invoice Entry"));
		}

		// Show Journal Entry status indicator
		if (frm.doc.journal_entry) {
			let indicator_color = 'blue';
			if (frm.doc.journal_entry_status === 'Submitted') {
				indicator_color = 'green';
			} else if (frm.doc.journal_entry_status === 'Cancelled') {
				indicator_color = 'red';
			} else if (frm.doc.journal_entry_status === 'Draft') {
				indicator_color = 'orange';
			}

			frm.dashboard.add_indicator(
				__('Journal Entry: {0} ({1})', [
					frm.doc.journal_entry,
					frm.doc.journal_entry_status || 'Draft'
				]),
				indicator_color
			);
		}

		// =========================================================
		// FIELD REQUIREMENTS
		// =========================================================
		if (frm.doc.purpose == "Employee Salary") {
			frm.toggle_reqd("branch", true);
			frm.toggle_reqd("fiscal_year", true);
			frm.toggle_reqd("month", true);
		}
	},

	// =========================================================
	// GET EMPLOYEE DETAILS
	// =========================================================
	get_employee_details: function (frm) {
		// Validate required fields
		if (!frm.doc.company) {
			frappe.msgprint(__("Company is required"));
			return;
		}

		if (!frm.doc.fiscal_year) {
			frappe.msgprint(__("Fiscal Year is required"));
			return;
		}

		if (!frm.doc.month) {
			frappe.msgprint(__("Month is required"));
			return;
		}

		if (!frm.doc.branch) {
			frappe.msgprint(__("Branch is required for MR employees"));
			return;
		}

		return frappe
			.call({
				doc: frm.doc,
				method: "fill_employee_details",
				freeze: true,
				freeze_message: __("Fetching MR Employees from MR Invoice Entry"),
			})
			.then((r) => {
				if (r.docs?.[0]?.employees) {
					frm.dirty();
					frm.save();
					frappe.msgprint(__("{0} MR employees fetched successfully", [r.docs[0].employees.length]));
				}
				frm.refresh();
				frm.scroll_to_field("employees");
			});
	},

	// =========================================================
	// PURPOSE CHANGE HANDLER
	// =========================================================
	purpose: function (frm) {
		if (frm.doc.docstatus == 0 && in_list(["Other Invoice", "Leave Encashment", "Overtime"], frm.doc.purpose)) {
			frm.add_custom_button(__('Get Invoices'), (doc) => {
				get_invoices(frm);
			}).addClass("btn-primary")
		}

		frm.clear_table("items");
		frm.refresh_field("items");
		frm.set_value('total_bill_amount', 0);
		frm.set_value('total_tax_amount', 0);

		// Clear employees when purpose changes
		if (frm.doc.purpose != "Employee Salary") {
			frm.clear_table("employees");
			frm.refresh_field("employees");
		}

		// Make fields required for Employee Salary purpose
		if (frm.doc.purpose == "Employee Salary") {
			frm.toggle_reqd("branch", true);
			frm.toggle_reqd("fiscal_year", true);
			frm.toggle_reqd("month", true);
		} else {
			frm.toggle_reqd("branch", false);
			frm.toggle_reqd("fiscal_year", false);
			frm.toggle_reqd("month", false);
		}
	},

	// =========================================================
	// COMPANY CHANGE - Clear dependent fields
	// =========================================================
	company: function (frm) {
		frm.set_value('branch', '');
		frm.set_value('cost_center', '');
	},

	// =========================================================
	// FISCAL YEAR CHANGE - Clear month
	// =========================================================
	fiscal_year: function (frm) {
		frm.set_value('month', '');
	},

	// =========================================================
	// BRANCH CHANGE - Clear month
	// =========================================================
	branch: function (frm) {
		frm.set_value('month', '');
	},

	// =========================================================
	// BULK LEAVE ENCASHMENT - Auto-fetch totals
	// =========================================================
	bulk_leave_encashment: function (frm) {
		if (frm.doc.bulk_leave_encashment && frm.doc.purpose === "Bulk Leave Encashment") {
			frappe.db.get_doc('Bulk Leave Encashment', frm.doc.bulk_leave_encashment).then(doc => {
				let total_bill_amount = 0;
				let total_tds_amount = 0;
				(doc.items || []).forEach(item => {
					total_bill_amount += flt(item.encashment_amount);
					total_tds_amount += flt(item.encashment_tax);
				});
				frm.set_value('total_bill_amount', total_bill_amount);
				frm.set_value('total_tax_amount', total_tds_amount);
			});
		}
	}
});

// =========================================================
// CHILD TABLE: TDS Remittance Item
// =========================================================
frappe.ui.form.on('TDS Remittance Item', {
	items_remove: (frm, cdt, cdn) => {
		let tds_amount = 0
		let bill_amount = 0
		frm.doc.items.map(v => {
			tds_amount += flt(v.tds_amount)
			bill_amount += flt(v.bill_amount)
		})
		frm.set_value('total_bill_amount', bill_amount)
		frm.set_value('total_tax_amount', tds_amount)
	}
})

// =========================================================
// HELPER FUNCTION: Get Invoices
// =========================================================
var get_invoices = function (frm) {
	if (in_list(["Other Invoice", "Leave Encashment", "Overtime"], frm.doc.purpose)) {
		frm.clear_table("items");
		frm.refresh_field("items");
		frm.set_value('total_bill_amount', 0);
		frm.set_value('total_tax_amount', 0);

		frappe.call({
			method: "get_invoices",
			doc: frm.doc,
			callback: function (r, rt) {
				frm.set_value('total_bill_amount', r.message[0]);
				frm.set_value('total_tax_amount', r.message[1]);
				frm.refresh_field("items");
				frm.refresh_fields();
			},
			freeze: true,
			freeze_message: "Loading Payment Invoices..... Please Wait"
		});
	}
}