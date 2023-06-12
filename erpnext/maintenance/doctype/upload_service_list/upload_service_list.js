// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Upload Service List', {
	refresh: function(frm) {
		frm.disable_save();
		show_upload(frm);
	},
	get_template:function(frm) {
		window.location.href = repl(frappe.request.url +
				'?cmd=%(cmd)s', {
						cmd: "erpnext.maintenance.doctype.upload_service_list.upload_service_list.get_template",
				});
	},
});

function show_upload(frm) {
	var me = this;
	var $wrapper = $(cur_frm.fields_dict.upload_html.wrapper).empty();
	frappe.upload.make({
			parent: $wrapper,
			args: {
					method: 'erpnext.maintenance.doctype.upload_service_list.upload_service_list.upload'
			},
			sample_url: "e.g. http://xx.com/somefile.csv",
			callback: function(attachment, r) {
					var $log_wrapper = $(cur_frm.fields_dict.import_log.wrapper).empty();

					if(!r.messages) r.messages = [];
					if(r.exc || r.error) {
							r.messages = $.map(r.message.messages, function(v) {
									var msg = v.replace("Inserted", "Valid")
											.replace("Updated", "Valid").split("<");
									if (msg.length > 1) {
											v = msg[0] + (msg[1].split(">").slice(-1)[0]);
									} else {
											v = msg[0];
									}
									return v;
							});

							r.messages = ["<h4 style='color:red'>"+__("Import Failed!")+"</h4>"]
									.concat(r.messages)
					} else {
							r.messages = ["<h4 style='color:green'>"+__("Import Successful!")+"</h4>"].
									concat(r.message.messages)
					}

					$.each(r.messages, function(i, v) {
							var $p = $('<p>').html(v).appendTo($log_wrapper);
							if(v.substr(0,5)=='Error') {
									$p.css('color', 'red');
							} else if(v.substr(0,8)=='Inserted') {
									$p.css('color', 'green');
							} else if(v.substr(0,7)=='Updated') {
									$p.css('color', 'green');
							} else if(v.substr(0,5)=='Valid') {
									$p.css('color', '#777');
							}
					});
			}
	});
	$wrapper.find('form input[type="submit"]')
			.attr('value', 'Upload and Import')
}
