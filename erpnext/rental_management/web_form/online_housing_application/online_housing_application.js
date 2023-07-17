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
					if(r.message[0]['middleName']){
						var applicant_name = r.message[0]['firstName'] + " " + r.message[0]['middleName'] + " " + r.message[0]['lastName'];
					}
					else{
						var applicant_name = r.message[0]['firstName'] + " " + r.message[0]['lastName'];
					}
					
					// Handle the response from the server
					if(r.message) {
						const nameField = $('[data-fieldname="applicant_name"]');
						const genderField = $('[data-fieldname="gender"]');
						const dzongkhagField = $('[data-fieldname="dzongkhag"]');
						const gewogField = $('[data-fieldname="gewog"]');
						const villageField = $('[data-fieldname="village"]');

                		nameField.val(applicant_name);
						genderField.val(r.message[0]['gender']=="M"?"Male":"Female");
						dzongkhagField.val(r.message[0]['dzongkhagName']);
						gewogField.val(r.message[0]['gewogName']);
						villageField.val(r.message[0]['permanentVillagename']);
					}else{
						frappe.throw("No such CID details found")
					}
				},
			});
		}
	}); 

	// Auto Populate details if the applicant it civil servant
	frappe.web_form.on('employment_type', (field, value) => {
		console.log(value);
		if(value=="Civil Servant"){
			var cid =  $('[data-fieldname="cid"]').val();
			frappe.call({
				method: 'erpnext.rental_management.doctype.api_setting.api_setting.get_civil_servant_detail',
				args: {
					cid: cid,
				},
				callback: function(r) {
					// Handle the response from the server
					if(r.message) {
						const nameField = $('[data-fieldname="designation"]');
						const genderField = $('[data-fieldname="ministry_agency"]');
						const dzongkhagField = $('[data-fieldname="grade"]');
						const gewogField = $('[data-fieldname="department"]');
						const villageField = $('[data-fieldname="village"]');

                		nameField.val(applicant_name);
						genderField.val(r.message[0]['gender']=="M"?"Male":"Female");
						dzongkhagField.val(r.message[0]['dzongkhagName']);
						gewogField.val(r.message[0]['gewogName']);
						villageField.val(r.message[0]['permanentVillagename']);
					}else{
						frappe.throw("No such CID details found")
					}
				},
			});

		}
	});


});
/*

"citizendetail": [
	{
		"cidNumber": "10808003482",
		"firstissueDate": "16/11/2022",
		"gender": "F",
		"dob": "31/05/2022",
		"fatherName": "Thukten  Dendup",
		"firstName": "Kinley ",
		"middleName": "",
		"lastName": "Choden",
		"mobileNumber": null,
		"motherName": "Tshering  Pelden",
		"occupationDesc": "Dependent",
		"dzongkhagSerialno": "8",
		"gewogSerialno": "81",
		"gewogName": "Shaba",
		"permanentHouseno": "Nya-8-Nil/45",
		"permanentThramno": "1423 (SHA-2933)",
		"permanentVillageserialno": "1958",
		"permanentVillagename": "Shungkarna",
		"palceOfbirth": "H",
		"countryName": null,
		"firstNamebh": "ཀུན་ལེགས་ ཆོས་སྒྲོན།",
		"middleNamebh": null,
		"lastNamebh": null,
		"householdNo": "080800237",
		"dzongkhagName": "Paro"
	}
*/

