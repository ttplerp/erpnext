// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Payroll Entry', {
	onload: function (frm) {
		frm.set_query('training_management', function(doc) {
			return {
				filters: {
					"course_cost_center": doc.cost_center,
					"status": "On Going",
				}
			};
		});
		frm.set_query('desuup_deployment', function(doc) {
			return {
				filters: {
					"cost_center": doc.cost_center,
					"deployment_status": "On Going",
				}
			};
		});
	},
	refresh: function(frm) {
		if (frm.doc.docstatus == 0) {
			frm.set_intro("");
			if(!frm.is_new() && !frm.doc.desuup_pay_slips_created) {
				frm.page.clear_actions_menu();
				frm.page.clear_primary_action();
				if(!frm.doc.successful) {
					frm.page.add_action_item(__("Get Desuup Details"), function() {
						frm.events.get_desuup_details(frm);
					});
				}
				if ((frm.doc.items || []).length) {
					frm.page.add_action_item(__('Create Pay Slips'), function() {
						frm.events.create_desuup_pay_slips(frm);
					});
				}
				if (frm.doc.successful) {
					// Cancel salary slips
					frm.page.add_action_item(__('Cancel Pay Slips'), function() {
						frm.save('Cancel').then(()=>{
							frm.page.clear_actions_menu();
							frm.page.clear_primary_action();
							frm.refresh();
							frm.events.refresh(frm);
						});
					});
				}
			} else if (frm.doc.desuup_pay_slips_created) {
				frm.page.clear_actions_menu();
				frm.page.clear_primary_action();
				if(!frm.doc.desuup_pay_slips_submitted){
					// Submit salary slips
					frm.page.add_action_item(__('Submit Pay Slips'), function() {
						frm.save('Submit').then(()=>{
							frm.page.clear_actions_menu();
							frm.page.clear_primary_action();
							frm.refresh();
							frm.events.refresh(frm);
						});
					});
				}
			}
		}
	},

	get_desuup_details: function (frm) {
		frm.set_value("number_of_desuups", 0);
		frm.refresh_field("number_of_desuups");
		return frappe.call({
			doc: frm.doc,
			method: 'get_desuup_details',
			callback: function(r) {
				if (r.message){
					frm.set_value("number_of_desuups", r.message);
					frm.refresh_field("number_of_desuups");
					frm.refresh_field("items");
					frm.dirty();

					// Following code commented by SHIV on 2020/10/20
					/*
					if(r.docs[0].validate_attendance){
						render_employee_attendance(frm, r.message);
					}
					*/
				}
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching Desuup Records...</span>'
		});
	},

	create_desuup_pay_slips: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "create_pay_slips",
			callback: function(r) {
				frm.refresh();
				frm.toolbar.refresh();
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Creating Salary Slips...</span>'
		})
	},

	fiscal_year: function (frm) {
		frm.events.clear_items_table(frm);
	},

	month_name: function (frm) {
		frm.events.clear_items_table(frm);
		frm.call({
			doc: frm.doc,
			method: "set_month_dates",
			callback: function(r) {
				frm.refresh_field("start_date");
				frm.refresh_field("end_date");
			},
		})
	},

	clear_items_table: function (frm) {
		frm.clear_table('items');
		frm.refresh();
	},
});

frappe.ui.form.on('Desuup Payroll Entry Item', {
    refresh: function(frm) {
        calculate_row_total(frm);
    },
    // Trigger calculations when the row is added
    items_add: function(frm) {
        calculate_row_total(frm);
    },
    // Recalculate totals when a row is removed from the items table
    items_remove: function(frm) {
        calculate_row_total(frm);
    },
    // Recalculate totals when a row field is changed
    items_on_form_rendered: function(frm) {
        calculate_row_total(frm);
    }
});

function calculate_row_total(frm) {
    let total_items_count = frm.doc.items ? frm.doc.items.length : 0;
    console.log(`Total items count: ${total_items_count}`);

    // Update the total_items_count field on the form
    frm.set_value('number_of_desuups', total_items_count);
    frm.refresh_field('number_of_desuups');
}
