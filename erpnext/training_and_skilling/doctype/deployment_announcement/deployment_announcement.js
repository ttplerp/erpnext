// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Deployment Announcement', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.deployment_created === 0 && ["Deployment", "Desuung National Service"].includes(frm.doc.type_of_deployment)) {
			frm.add_custom_button(__('Deployment'), function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.training_and_skilling.doctype.deployment_announcement.deployment_announcement.make_deployment",
					frm: cur_frm,
				})
			}, __('Create'));
		}
		if (frm.doc.docstatus === 1 && frm.doc.deployment_created === 0 && ["Skilling"].includes(frm.doc.type_of_deployment)) {
			frm.add_custom_button(__('Select Trainees'), function () {
				frappe.model.open_mapped_doc({
					method: "erpnext.training_and_skilling.doctype.deployment_announcement.deployment_announcement.make_training_selection",
					frm: cur_frm,
				})
			}, __('Create'));
		}
		frm.page.set_inner_btn_group_as_primary(__('Create'));

		frm.set_query("event", function(){
			if(frm.doc.type_of_deployment == "Skilling") {
				return {
					filters: {
						'end_date': [">", frappe.datetime.get_today()],
					}
				}
			} else {
				return {
					filters: {
						'disabled': 0,
					}
				}
			}

		})

		frm.set_query("category", function(){
			if(frm.doc.type_of_deployment == "Skilling") {
				return {
					 query: "erpnext.training_and_skilling.doctype.deployment_announcement.deployment_announcement.get_courses",
					 filters: {
						'cohort': frm.doc.event
					    }
				      }
			} else {
				return {
					filters: {
						'type_of_event': frm.doc.event,
						'disabled': 0,
					}
				}
			}
		})

		set_deployment_labels(frm);
	},
	type_of_deployment(frm) {
		set_deployment_labels(frm);
		frm.set_value({
		    event: null,
		    category: null
		});
	},

	onload:function(frm){
		frm.set_df_property("event", 'label', frm.doc.event_cohort)
		frm.set_df_property("category", 'label', frm.doc.category_course)
		frm.set_query("event", function(){
			return {
				filters: {
					'disabled': 0,
				}
			}
		})

		frm.set_query("category", function(){
			return {
				filters: {
					'type_of_event': frm.doc.event,
					'disabled': 0,
				}
			}
		})

		frm.set_query("dzongkhag", function(){
			return {
				filters: {
					'country_name': frm.doc.country,
					'disabled': 0,
				}
			}
		})

		frm.set_query("gewog", function(){
			return {
				filters: {
					'dzongkhag': frm.doc.dzongkhag,
					'disabled': 0,
				}
			}
		})
	},
	event: function(frm) {
		frappe.db.get_value('Cohort', frm.doc.event, 'end_date')
		    .then(r => {
			frm.set_value('registration_deadline', r.message.end_date);
		    });
		frm.set_value({
		    category: null
		});
	},
	category: function(frm) {
		if(!frm.doc.category) {
			frm.set_value('course_name', null);
			return;
		}
		if (frm.doc.type_of_deployment === "Skilling") {
			frappe.db.get_value('Course', frm.doc.category, 'course_name')
			    .then(r => {
				frm.set_value('course_name', r.message.course_name);
				frappe.call({
					method: "erpnext.training_and_skilling.doctype.deployment_announcement.deployment_announcement.get_course_details",
					args: {"cohort": frm.doc.event, "course": frm.doc.category}
				}).then(s => {
				console.log(s.message)
					frm.set_value('reporting_place', s.message.location);
					frm.set_value('training_center', s.message.training_center);
					frm.set_value('start_date', s.message.start_date);
					frm.set_value('end_date', s.message.end_date);
					frm.set_value('dzongkhag', s.message.dzongkhag);
					frm.set_value('gewog', s.message.gewog);
					frm.set_value('starttime', "09:00:00");
					frm.set_value('endtime', "17:00:00");
				    });
			    });
		} else {
			frm.set_value('course_name', null);
			frm.set_value('training_center', null);
		}
	}
});

function set_deployment_labels(frm) {
    const is_skilling = frm.doc.type_of_deployment === "Skilling";
    const event_label = is_skilling ? __("Cohort") : __("Type of Event");
    const category_label = is_skilling ? __("Course") : __("Category of Deployment");

    frm.set_df_property("event", "label", event_label);
    frm.set_df_property("category", "label", category_label);

    if (frm.doc.event_cohort !== event_label || frm.doc.category_course !== category_label) {
        frm.set_value({
            event_cohort: event_label,
            category_course: category_label
        });
    }
}
