frappe.ready(function() {
	// bind events here
	var applicant_cid = ""
	var spouse_cid = ""
	frappe.web_form.on('cid', (field, value) => {
		applicant_cid=value;
		if(value.length == "11"){
			// Example frappe.call usage
			get_cid_detail(applicant_cid, category="Applicant");
			if(employment_type=="Civil Servant"){
				get_employee_detail(applicant_cid, category="Applicant");
			}
		}
	}); 
	// Auto Populate details if the applicant it civil servant
	frappe.web_form.on('employment_type', (field, value) => {
		if(value=="Civil Servant"){
			get_employee_detail(applicant_cid, category="Applicant");
		}
	});

	frappe.web_form.on('spouse_cid', (field, value) => {
		spouse_cid = value
		if(value.length == "11"){
			get_cid_detail(spouse_cid, category="Spouse");
		}
	});
	// Auto Populate details if the applicant it civil servant
	frappe.web_form.on('spouse_employment_type', (field, value) => {
		if(value=="Civil Servant"){
			get_employee_detail(spouse_cid, category="Spouse");
		}
	});
});

function get_cid_detail(cid, category){
	frappe.call({
		method: 'erpnext.rental_management.doctype.api_setting.api_setting.get_cid_detail',
		args: {
			cid: cid,
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
				if(category=="Applicant"){
					$('[data-fieldname="applicant_name"]').val(applicant_name);
					$('[data-fieldname="gender"]').val(r.message[0]['gender']=="M"?"Male":"Female");
					$('[data-fieldname="dzongkhag"]').val(r.message[0]['dzongkhagName']);
					$('[data-fieldname="gewog"]').val(r.message[0]['gewogName']);
					$('[data-fieldname="village"]').val(r.message[0]['permanentVillagename']);
				}else if(category=="Spouse"){
					$('[data-fieldname="spouse_name"]').val(applicant_name);
					$('[data-fieldname="spouse_dzongkhag"]').val(r.message[0]['dzongkhagName']);
					$('[data-fieldname="spouse_gewog"]').val(r.message[0]['gewogName']);
					$('[data-fieldname="spouse_village"]').val(r.message[0]['permanentVillagename']);
					$('[data-fieldname="spouse_dob"]').val(r.message[0]['dob']);
				}
			}else{
				frappe.throw("No such CID details found")
			}
		},
	});
}

function get_employee_detail(applicant_cid, category){
	frappe.call({
		method: 'erpnext.rental_management.doctype.api_setting.api_setting.get_civil_servant_detail',
		args: {
			cid: applicant_cid,
		},
		callback: function(r) {
			// Handle the response from the server
			if(r.message) {
				if(category=="Applicant"){
					$('[data-fieldname="designation"]').val(r.message[0]['positionTitle']);
					$('[data-fieldname="ministry_agency"]').val(r.message[0]['OrganogramLevel1']);
					$('[data-fieldname="grade"]').val(r.message[0]['positionLevel']);
					$('[data-fieldname="department"]').val(r.message[0]['OrganogramLevel2']);
					$('[data-fieldname="employee_id"]').val(r.message[0]['employeeNumber']);
				} else if(category=="Spouse"){
					$('[data-fieldname="spouse_designation"]').val(r.message[0]['positionTitle']);
					$('[data-fieldname="spouse_ministry"]').val(r.message[0]['OrganogramLevel1']);
					$('[data-fieldname="spouse_grade"]').val(r.message[0]['positionLevel']);
					$('[data-fieldname="spouse_department"]').val(r.message[0]['OrganogramLevel2']);
					$('[data-fieldname="employee_id"]').val(r.message[0]['employeeNumber']);
				}
			}else{
				frappe.throw("No record found in Civil Servant DB for provided CID ")
			}
		},
	});
}

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

