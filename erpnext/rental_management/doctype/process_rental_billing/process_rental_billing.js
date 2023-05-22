// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.cscript.display_activity_log = function(msg) {
	if(!cur_frm.ss_html)
			cur_frm.ss_html = cur_frm.fields_dict['activity_log'].wrapper;
}

frappe.ui.form.on('Process Rental Billing', {
	refresh: function(frm) {
		frm.disable_save();
	},
	setup: function (frm) {
		frm.set_query("dzongkhag", function () {
			return {
				"filters": [
					["is_dzongkhag", "=", 1]
				]
			};
		});
		cur_frm.set_query("tenant", function() {
			return {
				"filters": [
					["dzongkhag", "=", frm.doc.dzongkhag]
				]
			};
		});
	},
	create_rental_bills: function(frm) {
		process_rental(frm, "create");
	},
	remove_rental_bills: function(frm) {
		process_rental(frm, "remove");
	},
	submit_rental_bills: function(frm) {
		process_rental(frm, "submit");
	}
});

var process_rental = function(frm, process_type){
	var head_log="", body_log="", msg="", msg_other="";
	cur_frm.cscript.display_activity_log('');
	head_log = '<div class="container"><h4>'+__("Activity Log 2:")+'</h4><table class="table">';
	frm.set_value("progress", "");
	frm.refresh_field("progress");

	if(frm.doc.ministry_agency && !frm.doc.dzongkhag){
		frappe.throw("Please select Dzongkhag first");
	}

	if (process_type == "create"){
			msg = "Creating Rental Bill(s).... Please Wait!!!";
			msg_other = "created";
	} else if(process_type == "remove"){
			msg = "Removing Rental Bill(s).... Please Wait!!!";
			msg_other = "removed";
	} else{
			msg = "Submitting Rental Bill(s).... Please Wait!!!";
			msg_other = "submitted";
	}

	return frappe.call({
		method: "get_tenant_list",
		doc: frm.doc,
		args: {"process_type": process_type},
		callback: function(r, rt){
			if(r.message.length != 0){
				console.log(r.message);
				var counter=0;
				r.message.forEach(function(rec) {
					console.log("Tenant: " + rec.name + "; Process type: " + process_type);
					// counter += 1;
					// frm.set_value("progress", "Processing "+counter+"/"+r.message.length+" rental bill(s) ["+Math.round((counter/r.message.length)*100)+"% completed]");
					// frm.refresh_field("progress");
					// frm.refresh_field("activity_log");
					cur_frm.call({
						method: "process_rental",
						doc: frm.doc,
						args: {"process_type": process_type, "name": rec.name},
						callback: function(r2, rt2){
							console.log("message :" + r2.message.msg);
							if(r2.message.flag){
								counter += 1;
							}
							frm.set_value("progress", "Processing "+counter+"/"+r.message.length+" rental bill(s) ["+Math.round((counter/r.message.length)*100)+"% completed]");
							frm.refresh_field("progress");
							frm.refresh_field("activity_log");		
							body_log = r2.message.msg+body_log
							cur_frm.ss_html.innerHTML = head_log+body_log
						},
						freeze: true,
					});
				});
			} else {
				body_log = '<div style="color:#fa3635;">No tenant for the above selected criteria OR Rental Bill(s) already '+msg_other+'</div>';
				msgprint(body_log);
				cur_frm.ss_html.innerHTML = head_log+body_log;
			}
		},
		freeze: true,
		freeze_message: msg,
	});
	cur_frm.ss_html.innerHTML += '</table></div>';
}