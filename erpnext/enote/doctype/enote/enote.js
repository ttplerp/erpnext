// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('eNote', {

	refresh: function (frm) {
		frm.set_df_property("permitted_user", "hidden", 1);
		
		frm.set_query("enote_series", function () {
			return {
				filters: {
					type: frm.doc.enote_type,
				},
			};
		});

		if(frm.doc.workflow_state == "Approved"){
			frm.set_df_property("forward_to","hidden", 1);
			frm.set_df_property("copied", "hidden", 0);
			frm.set_df_property("enote_format","hidden", 0);
			
		} else{
			frm.set_df_property("copied", "hidden", 1);
			frm.set_df_property("enote_format","hidden", 1);
		}

		if (frm.doc.__islocal) {
			frm.events.set_editable(frm, true);
		} else {
			if (!frm.doc.content) {
				frm.doc.content = "<span></span>";
			}
			// toggle edit
			if(frappe.session.user == frm.doc.permitted_user && frm.doc.workflow_state != "Approved" ){
				frm.add_custom_button(__("Edit Content"), function () {
					frm.events.set_editable(frm, !frm.is_note_editable);
				}, __("Activities"));
			}
			frm.events.set_editable(frm, false);
		}

		if(frappe.session.user == frm.doc.permitted_user && (frm.doc.workflow_state == "Pending" || frm.doc.workflow_state == "Rejected")){
			frm.add_custom_button(__('Write Remarks'), function(){
				let remark=""
				$.each(frm.doc.remark || [], function(i, item){
					if(frappe.session.user == item.user && (item.action === undefined || item.action === null)){
						remark=item.remark;
					}
				});				
				let d = new frappe.ui.Dialog({
					title: 'Write Your Remarks',
					fields: [
						{
							label: __(""),
							fieldtype: "Text Editor",
							fieldname: "content",
							default: remark,
						}
					],
					size: 'medium', // small, large, extra-large 
					primary_action_label: 'Save Remark',
					primary_action(values) {
						save_remark(frm, values['content']);
						d.hide();
					},
				});
				d.show();
			}, __("Activities"));
		}
	},
	set_editable: function (frm, editable) {
		// no permission
		if (editable && !frm.perm[0].write) return;

		$.each(frm.fields_dict, function(fieldname) {
			if(fieldname != "copied")
				frm.set_df_property(fieldname, "read_only", editable ? 0 : 1);
		});

		// no label, description for content either
		frm.get_field("content").toggle_label(editable);
		frm.get_field("content").toggle_description(editable);

		// set flag for toggle
		frm.is_note_editable = editable;
	},
});

frappe.ui.form.on("Note Remark", {
	restore_content: function(frm, cdt, cdn) {
		if(frm.doc.workflow_state != "Approved"){
			var d = frappe.get_doc(cdt, cdn);
			frappe.call({
				method: "restore_content",
				doc: frm.doc,
				args: {
					child_id: d.name
				},
				callback: function(r){
					cur_frm.reload_doc();
				},
				freeze: true,
				freeze_message: "Restoring the Note to this content .... Please Wait",
			});
		}else{
			frappe.msgprint("Restoring this Note is not allowed after submission")
		}
	},
});

frappe.ui.form.on("eNote Reviewer", {
	review: function (frm, cdt, cdn) {
		var doc = frappe.get_doc(cdt, cdn);
		if (doc.user_id == frappe.session.user) {
			let remark = ""
			let d = new frappe.ui.Dialog({
				title: 'Write Your Remarks',
				fields: [
					{
						label: __(""),
						fieldtype: "Text Editor",
						fieldname: "content",
						default: remark,
					}
				],
				size: 'medium', // small, large, extra-large 
				primary_action_label: 'Review',
				primary_action(values) {
					save_remark(frm, values['content'], 1);
					d.hide();
				},
			});
			d.show();
		} else { 
			frappe.throw("You cannot review instead of others.")
		}
	},
});

var save_remark = function(frm, remark, reviewers){
	frappe.call({
		method: "save_remark",
		doc: frm.doc,
		args: {
			remark: remark,
			reviewers: reviewers
		},
		callback: function(r){
			cur_frm.reload_doc();
		},
		freeze: true,
        freeze_message: "Saving Remarks.... Please Wait",
	})
}