// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Desuup Attendance Tool', {
	refresh: function(frm) {
		frm.disable_save();
	},

	onload: function(frm) {
		frm.set_value("date", frappe.datetime.get_today());
		// erpnext.desuup_attendance_tool.load_desuups(frm);

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

	date: function(frm) {
		erpnext.desuup_attendance_tool.load_desuups(frm);
	},

	cost_center: function(frm) {
		erpnext.desuup_attendance_tool.load_desuups(frm);
	},

	training_management: function(frm) {
		erpnext.desuup_attendance_tool.load_desuups(frm);
	},

	desuup_deployment: function(frm) {
		erpnext.desuup_attendance_tool.load_desuups(frm);
	},

	domain: function(frm) {
		erpnext.desuup_attendance_tool.load_desuups(frm);
	},

	programme: function(frm) {
		erpnext.desuup_attendance_tool.load_desuups(frm);
	},
	
	training_center: function(frm) {
		erpnext.desuup_attendance_tool.load_desuups(frm);
	},
});

erpnext.desuup_attendance_tool = {
	load_desuups: function(frm) {
		if (frm.doc.date) {
			frappe.call({
				method: "erpnext.training_and_skilling.doctype.desuup_attendance_tool.desuup_attendance_tool.get_desuups",
				args: {
					date: frm.doc.date,
					attendance_for: frm.doc.attendance_for,
					cost_center: frm.doc.cost_center,
					training_management: frm.doc.training_management,
					desuup_deployment: frm.doc.desuup_deployment,
					programme: frm.doc.programme,
					domain: frm.doc.domain,
					training_center: frm.doc.training_center,
					company: frm.doc.company,
				},
				callback: function(r) {
					if(r.message['unmarked'].length > 0) {
						unhide_field('unmarked_attendance_section')
						if(!frm.desuup_area) {
							frm.desuup_area = $('<div>')
							.appendTo(frm.fields_dict.desuups_html.wrapper);
						}
						frm.DesuupSelector = new erpnext.DesuupSelector(frm, frm.desuup_area, r.message['unmarked'])
					}
					else{
						hide_field('unmarked_attendance_section')
					}

					if(r.message['marked'].length > 0) {
						unhide_field('marked_attendance_section')
						if(!frm.marked_desuup_area) {
							frm.marked_desuup_area = $('<div>')
								.appendTo(frm.fields_dict.marked_attendance_html.wrapper);
						}
						frm.marked_desuup = new erpnext.MarkedDesuup(frm, frm.marked_desuup_area, r.message['marked'])
					}
					else{
						hide_field('marked_attendance_section')
					}
				}
			});
		}
	}
}

erpnext.MarkedDesuup = class MarkedDesuup {
	constructor(frm, wrapper, desuup) {
		this.wrapper = wrapper;
		this.frm = frm;
		this.make(frm, desuup);
	}
	make(frm, desuup) {
		var me = this;
		$(this.wrapper).empty();

		var row;
		$.each(desuup, function(i, m) {
			var attendance_icon = "fa fa-check";
			var color_class = "";
			if(m.status == "Absent") {
				attendance_icon = "fa fa-times"
				color_class = "text-muted";
			}
			else if(m.status == "Half Day") {
				attendance_icon = "fa fa-minus"
			}

			if (i===0 || i % 4===0) {
				row = $('<div class="row"></div>').appendTo(me.wrapper);
			}

			$(repl('<div class="col-sm-3 %(color_class)s">\
				<label class="marked-desuup-label"><span class="%(icon)s"></span>\
				%(desuup)s</label>\
				</div>', {
					desuup: m.desuup +' : '+ m.desuup_name,
					icon: attendance_icon,
					color_class: color_class
				})).appendTo(row);
		});
	}
};

erpnext.DesuupSelector = class DesuupSelector {
	constructor(frm, wrapper, desuup) {
		this.wrapper = wrapper;
		this.frm = frm;
		this.make(frm, desuup);
	}
	make(frm, desuup) {
		var me = this;

		$(this.wrapper).empty();
		var desuup_toolbar = $('<div class="col-sm-12 top-toolbar">\
		<button class="btn btn-default btn-add btn-xs"></button>\
		<button class="btn btn-xs btn-default btn-remove"></button>\
		</div>').appendTo($(this.wrapper));

		var mark_desuup_toolbar = $('<div class="col-sm-12 bottom-toolbar">\
			<button class="btn btn-primary btn-mark-present btn-xs"></button>\
			<button class="btn btn-danger btn-mark-absent btn-xs"></button>\
			<button class="btn btn-warning btn-mark-half-day btn-xs"></button>\
			</div>');

		desuup_toolbar.find(".btn-add")
			.html(__('Check all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if(!$(check).is(":checked")) {
						check.checked = true;
					}
				});
			});

		desuup_toolbar.find(".btn-remove")
			.html(__('Uncheck all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						check.checked = false;
					}
				});
			});

		mark_desuup_toolbar.find(".btn-mark-present")
			.html(__('Mark Present'))
			.on("click", function() {
				var desuup_present = [];
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						desuup_present.push(desuup[i]);
					}
				});
				frappe.call({
					method: "erpnext.training_and_skilling.doctype.desuup_attendance_tool.desuup_attendance_tool.mark_desuup_attendance",
					args:{
						"desuup_list":desuup_present,
						"status":"Present",
						"date":frm.doc.date,
						"attendance_for":frm.doc.attendance_for,
						"company":frm.doc.company
					},

					callback: function(r) {
						erpnext.desuup_attendance_tool.load_desuups(frm);

					}
				});
			});

		mark_desuup_toolbar.find(".btn-mark-absent")
			.html(__('Mark Absent'))
			.on("click", function() {
				var desuup_absent = [];
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						desuup_absent.push(desuup[i]);
					}
				});
				frappe.call({
					method: "erpnext.training_and_skilling.doctype.desuup_attendance_tool.desuup_attendance_tool.mark_desuup_attendance",
					args:{
						"desuup_list":desuup_absent,
						"status":"Absent",
						"date":frm.doc.date,
						"attendance_for":frm.doc.attendance_for,
						"company":frm.doc.company
					},

					callback: function(r) {
						erpnext.desuup_attendance_tool.load_desuups(frm);

					}
				});
			});

		mark_desuup_toolbar.find(".btn-mark-half-day")
			.html(__('Mark Half Day'))
			.on("click", function() {
				var desuup_half_day = [];
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						desuup_half_day.push(desuup[i]);
					}
				});
				frappe.call({
					method: "erpnext.training_and_skilling.doctype.desuup_attendance_tool.desuup_attendance_tool.mark_desuup_attendance",
					args:{
						"desuup_list":desuup_half_day,
						"status":"Half Day",
						"date":frm.doc.date,
						"attendance_for":frm.doc.attendance_for,
						"company":frm.doc.company
					},

					callback: function(r) {
						erpnext.desuup_attendance_tool.load_desuups(frm);

					}
				});
			});

		var row;
		$.each(desuup, function(i, m) {
			if (i===0 || (i % 4)===0) {
				row = $('<div class="row"></div>').appendTo(me.wrapper);
			}

			$(repl('<div class="col-sm-3 unmarked-desuup-checkbox">\
				<div class="checkbox">\
				<label><input type="checkbox" class="desuup-check" desuup="%(desuup)s"/>\
				%(desuup)s</label>\
				</div></div>', {desuup: m.desuup +' : '+ m.desuup_name})).appendTo(row);
		});

		mark_desuup_toolbar.appendTo($(this.wrapper));
	}
};