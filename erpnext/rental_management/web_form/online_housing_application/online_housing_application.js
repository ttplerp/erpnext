frappe.ready(function() {
	// bind events here
	frappe.web_form.on('cid', (field, value) => {
		if(value.length == "11"){
			// Example frappe.call usage
			frappe.call({
				method: 'erpnext.rental_management.doctype.api_setting.api_setting.get_cid_detail',
				args: {
					cid: value,
				},
				callback: function(r) {
					console.log(r.message);
					// Handle the response from the server
					if(r.message) {
						const resultField = $('[data-fieldname="applicant_name"]');
                		resultField.val(r.message.name);
					}else{
						frappe.throw("No such CID details found")
					}
				},
			});
		}
	}); 
});

