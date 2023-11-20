frappe.ready(function() {
	// bind events here
	var applicant_cid = ""
	frappe.web_form.on('cid', (field, value) => {
		applicant_cid=value;
		if(value.length == "11"){
			// Example frappe.call usage
			get_cid_detail(applicant_cid);
		}
	}); 
})

function get_cid_detail(cid){
	frappe.call({
		method: 'erpnext.rental_management.doctype.api_setting.api_setting.get_cid_detail',
		args: {
			cid: cid,
		},
		callback: function(r) {
			if(r.message['middleName']){
				var applicant_name = r.message['firstName'] + " " + r.message['middleName'] + " " + r.message['lastName'];
			}
			else{
				var applicant_name = r.message['firstName'] + " " + r.message['lastName'];
			}
			
			//Handle the response from the server
			if(r.message) {
				$('[data-fieldname="applicant_name"]').val(applicant_name);		
			}else{
				frappe.throw("No such CID details found")
			}
		},
	});
}