// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CBS Entry', {
	// refresh: function(frm) {

	// },
	refresh: function(frm){
		if (frm.doc.docstatus == 1 && frm.doc.cbs_status == "FAILURE"){
			frm.add_custom_button(__('Retry CBS Posting'), ()=>{
				frappe.call({
					method: "retry_cbs_posting",
					doc: frm.doc
				});
			}).addClass("btn-primary custom-create custom-create-css");
		}
		if(frm.doc.file_details && frm.doc.file_details != "None"){
			frm.add_custom_button(__('Download File'), function() {
				var file_url = frm.doc.file_details;
				if (frm.doc.file_details) {
					file_url = file_url.replace(/#/g, '%23');
				}
				window.open(file_url);
			}, "fa fa-download").addClass('btn-primary');
		}
	}
});
