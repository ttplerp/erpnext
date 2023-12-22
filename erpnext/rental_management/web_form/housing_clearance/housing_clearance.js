frappe.ready(function() {
	// bind events here
	// var applicant_cid = ""
	// frappe.web_form.on('cid', (field, value) => {
	// 	applicant_cid=value;
	// 	const applicant_type = frappe.web_form.get_value('applicant_type');
		
			
	// 		if(value.length == '11'){
	// 			if (applicant_type=="Bhutanese"){
	// 				// Example frappe.call usage
	// 			// get_cid_detail(applicant_cid);
	// 			frappe.throw("Bhutan")
	// 			}
				
	// 	}
		
		
		
	// }); 


	frappe.web_form.on('applicant_type', (field, value) => {

	if (value==="Non-Bhutanese"){
			frappe.web_form.set_df_property('cid', 'label', 'Work Permit No');
		}	
	if (value==="Organisation"){
			frappe.web_form.set_df_property('cid', 'label', 'Organisation No');
		}
    if (value === "Bhutanese") {
		
		frappe.web_form.set_df_property('cid', 'label', 'Citizen ID No');
        frappe.web_form.on('cid', (field, value) => {
            if (value.length === 11) {
                // frappe.throw(applicant_cid);
				console.log(value)
				get_cid_detail(value);
            }
        });
	

    // } else {
    //     let typingTimer;
    //     const timeoutDuration = 2000;
    //     const inputField = document.querySelector('[data-fieldname="cid"]');
		

    //     inputField.addEventListener('input', function(event) {
    //         clearTimeout(typingTimer);
	// 		const inputValue = frappe.web_form.get_value('cid');

    //         typingTimer = setTimeout(() => {
    //             //  frappe.throw(inputValue);
	// 			console.log(inputValue)
	// 			get_cid_detail(inputValue);
    //         }, timeoutDuration);
	// 	});
	}
    
});


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
				$('[data-fieldname="application_name"]').val(applicant_name);		
			}else{
				frappe.throw("No such CID details found")
			}
		},
	});
}
});