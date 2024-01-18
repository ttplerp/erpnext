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
			frappe.web_form.set_value('gross_salary_info', 'Your gross salary will be fetched from EPEMS.');
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
			frappe.web_form.set_value('spouse_gross_salary_info', 'Your spouse gross salary will be fetched from EPEMS.');
			
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
			if(r.message['middleName']){
				var applicant_name = r.message['firstName'] + " " + r.message['middleName'] + " " + r.message['lastName'];
			}
			else{
				var applicant_name = r.message['firstName'] + " " + r.message['lastName'];
			}
			
			// Handle the response from the server
			if(r.message) {
				if(category=="Applicant"){
					$('[data-fieldname="applicant_name"]').val(applicant_name);
					$('[data-fieldname="gender"]').val(r.message['gender']=="M"?"Male":"Female");
					$('[data-fieldname="dzongkhag"]').val(r.message['dzongkhagName']);
					$('[data-fieldname="gewog"]').val(r.message['gewogName']);
					$('[data-fieldname="village"]').val(r.message['permanentVillagename']);
					var [day, month, year] = r.message['dob'].split('/');
var formattedDate = `${year}-${month}-${day}`;

$('[data-fieldname="date_of_birth"]').val(formattedDate);
frappe.web_form.set_value('date_of_birth',formattedDate);
				}else if(category=="Spouse"){
					$('[data-fieldname="spouse_name"]').val(applicant_name);
					$('[data-fieldname="spouse_dzongkhag"]').val(r.message['dzongkhagName']);
					$('[data-fieldname="spouse_gewog"]').val(r.message['gewogName']);
					$('[data-fieldname="spouse_village"]').val(r.message['permanentVillagename']);
					$('[data-fieldname="spouse_dob"]').val(r.message['dob']);
					frappe.web_form.set_value('spouse_dob',r.message['dob']);
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
			console.log(r.message);
			if(r.message) {
				if(category=="Applicant"){
					$('[data-fieldname="designation"]').val(r.message['positionTitle']);
					$('[data-fieldname="ministry_agency"]').val(r.message['OrganogramLevel1']);
					$('[data-fieldname="grade"]').val(r.message['positionLevel']);
					$('[data-fieldname="department"]').val(r.message['OrganogramLevel2']);
					$('[data-fieldname="employee_id"]').val(r.message['employeeNumber']);
					$('[data-fieldname="gross_salary"]').val(r.message['GrossPay']);
					$('[data-fieldname="email_id"]').val(r.message['Email']);
					$('[data-fieldname="mobile_no"]').val(r.message['MobileNo']);
					
				} else if(category=="Spouse"){
					$('[data-fieldname="spouse_designation"]').val(r.message['positionTitle']);
					$('[data-fieldname="spouse_ministry"]').val(r.message['OrganogramLevel1']);
					$('[data-fieldname="spouse_grade"]').val(r.message['positionLevel']);
					$('[data-fieldname="spouse_department"]').val(r.message['OrganogramLevel2']);
					$('[data-fieldname="employee_id"]').val(r.message['employeeNumber']);
					$('[data-fieldname="spouse_gross_salary"]').val(r.message['GrossPay']);
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

