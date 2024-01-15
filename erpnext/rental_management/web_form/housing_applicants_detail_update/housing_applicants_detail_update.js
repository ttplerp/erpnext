frappe.ready(function() {
    // bind events here

	



	//Setting date and time to now
	var today = frappe.datetime.get_today();
	$('[data-fieldname="application_date_and_time"]').val(today);

	//checking if cid exist in Housing application

	let typingTimer;
	    const timeoutDuration = 2000;
	    const inputField = document.querySelector('[data-fieldname="cid"]');
		

	    inputField.addEventListener('input', function(event) {
	        clearTimeout(typingTimer);
			const inputValue = frappe.web_form.get_value('cid');

	        typingTimer = setTimeout(() => {
	            //  frappe.throw(inputValue);
				console.log(inputValue)
				checkCidExistence(inputValue)
				
	        }, timeoutDuration);
		});

	// frappe.web_form.on('cid',(field,value)=>{

	


	// 	if(value.length==11){
	// 		checkCidExistence(value)
	// 	}


	// });

	


	


	frappe.web_form.on('marital_status',(field,value)=>{
		if(value=='Married'){
			let cid;
			//frappe.web_form.set_value('spouse_citizen_id', 'hahahahahah');

			frappe.web_form.on('spouse_citizen_id',(field,value)=>{
				cid = value

				if(value.length==11){
					// frappe.throw("Fetching data from census api")
					get_cid_detail(value)
				}
		
			});

			frappe.web_form.on('spouse_employment_type',(field,value)=>{
				
				frappe.web_form.set_value('spouse_employee_id', '');
				frappe.web_form.set_value('spouse_ministryagency', '');
				frappe.web_form.set_value('spouse_designation', '');
				frappe.web_form.set_value('spouse_name_of_agency', '');
				frappe.web_form.set_value('spouse_grade', '');
				frappe.web_form.set_value('spouse_gross_salary', '');
				


				if(value=='Civil Servant'){
					// frappe.throw(cid)
					get_employee_detail(cid)
					frappe.web_form.set_value('spouse_gross_salary_info', 'Your spouse gross salary will be fetched from EPEMS.');
				}
		
			});

			
		}
	});
})


function checkCidExistence(cid){
	
	frappe.call({
		method: 'erpnext.rental_management.doctype.housing_application_details_update.housing_application_details_update.checkCidExistence',
		
		args: {
			cid: cid,
		},
		callback: function(r) {
			
			if (r.message === true){
				getApplicantDetails(cid)
			}
			else{
				frappe.web_form.set_value('cid', '');
				frappe.web_form.set_value('applicant_name', '');
				frappe.web_form.set_value('gender', '');
				frappe.web_form.set_value('marital_status', '');
				frappe.throw("You haven't applied for housing before")

			}
			}
		
	});
}

function getApplicantDetails(cid){
//console.log(cid)
frappe.call({
	method: 'erpnext.rental_management.doctype.housing_application_details_update.housing_application_details_update.getApplicantDetails',
	
	args: {
		cid: cid,
	},
	callback: function(r) {
		// console.log(r.message)
	
		const applicant_name = r.message[0].applicant_name;
		const gender = r.message[0].gender;
		const marital_status = r.message[0].marital_status;
		const mobile_no = r.message[0].mobile_no;
		const date_of_birth = r.message[0].date_of_birth;
		const spouse_citizen_id = r.message[0].spouse_cid;

		const spouse_name = r.message[0].spouse_name;
		const spouse_dzongkhag = r.message[0].spouse_dzongkhag;
		const spouse_gewog = r.message[0].spouse_gewog;
		const spouse_dob = r.message[0].spouse_dob;
		const spouse_village = r.message[0].spouse_village;
		const spouse_employment_type = r.message[0].spouse_employment_type;
		const spouse_employee_id = r.message[0].spouse_employee_id;
		const spouse_ministry = r.message[0].spouse_ministry;
		const spouse_designation = r.message[0].spouse_designation;
		const spouse_agency = r.message[0].spouse_agency;
		const spouse_grade = r.message[0].spouse_grade;
		const spouse_gross_salary = r.message[0].spouse_gross_salary;
		
		
	
		frappe.web_form.set_value('applicant_name', applicant_name);
		frappe.web_form.set_value('gender', gender);
		frappe.web_form.set_value('marital_status', marital_status);
		frappe.web_form.set_value('mobile_no', mobile_no);
		frappe.web_form.set_value('spouse_citizen_id', spouse_citizen_id);

		frappe.web_form.set_value('spouse_name', spouse_name);
		frappe.web_form.set_value('spouse_dzongkhag', spouse_dzongkhag);
		frappe.web_form.set_value('spouse_gewog', spouse_gewog);
		frappe.web_form.set_value('spouse_date_of_birth', spouse_dob);
		frappe.web_form.set_value('spouse_village', spouse_village);
		frappe.web_form.set_value('spouse_employment_type', spouse_employment_type);
		frappe.web_form.set_value('spouse_employee_id', spouse_employee_id);
		frappe.web_form.set_value('spouse_ministryagency', spouse_ministry);
		frappe.web_form.set_value('spouse_designation', spouse_designation);
		frappe.web_form.set_value('spouse_name_of_agency', spouse_agency);
		frappe.web_form.set_value('spouse_grade', spouse_grade);
		frappe.web_form.set_value('spouse_gross_salary', spouse_gross_salary);
		frappe.web_form.set_value('date_of_birth', date_of_birth);
		
		
		
		}
	
});
}

//fetch the details of the spouse
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
			
			// Handle the response from the server
			if(r.message) {
				// if(category=="Applicant"){
				// 	$('[data-fieldname="applicant_name"]').val(applicant_name);
				// 	$('[data-fieldname="gender"]').val(r.message['gender']=="M"?"Male":"Female");
				// 	$('[data-fieldname="dzongkhag"]').val(r.message['dzongkhagName']);
				// 	$('[data-fieldname="gewog"]').val(r.message['gewogName']);
				// 	$('[data-fieldname="village"]').val(r.message['permanentVillagename']);
				// }else if(category=="Spouse"){
					$('[data-fieldname="spouse_name"]').val(applicant_name);
					$('[data-fieldname="spouse_dzongkhag"]').val(r.message['dzongkhagName']);
					$('[data-fieldname="spouse_gewog"]').val(r.message['gewogName']);
					$('[data-fieldname="spouse_village"]').val(r.message['permanentVillagename']);
					$('[data-fieldname="spouse_date_of_birth"]').val(r.message['dob']);
				// }
			}else{
				frappe.throw("No such CID details found")
			}
		},
	});
}


//fetch data from rcsc api
function get_employee_detail(applicant_cid){
	frappe.call({
		method: 'erpnext.rental_management.doctype.api_setting.api_setting.get_civil_servant_detail',
		args: {
			cid: applicant_cid,
		},
		callback: function(r) {
			// Handle the response from the server
			console.log(applicant_cid);
			if(r.message) {
				// if(category=="Applicant"){
				// 	$('[data-fieldname="designation"]').val(r.message['positionTitle']);
				// 	$('[data-fieldname="ministry_agency"]').val(r.message['OrganogramLevel1']);
				// 	$('[data-fieldname="grade"]').val(r.message['positionLevel']);
				// 	$('[data-fieldname="department"]').val(r.message['OrganogramLevel2']);
				// 	$('[data-fieldname="employee_id"]').val(r.message['employeeNumber']);
				// 	$('[data-fieldname="gross_salary"]').val(r.message['GrossPay']);
				// 	$('[data-fieldname="email_id"]').val(r.message['Email']);
				// 	$('[data-fieldname="mobile_no"]').val(r.message['MobileNo']);
				// } else if(category=="Spouse"){
					
					$('[data-fieldname="spouse_designation"]').val(r.message['positionTitle']);
					$('[data-fieldname="spouse_ministryagency"]').val(r.message['OrganogramLevel1']);
					$('[data-fieldname="spouse_grade"]').val(r.message['positionLevel']);
					$('[data-fieldname="spouse_department"]').val(r.message['OrganogramLevel2']);
					$('[data-fieldname="spouse_employee_id"]').val(r.message['employeeNumber']);
					$('[data-fieldname="spouse_gross_salary"]').val(r.message['GrossPay']);
					frappe.web_form.set_value('spouse_gross_salary',r.message['GrossPay']);
				// }
			}else{
				frappe.throw("No record found in Civil Servant DB for provided CID ")
			}
		},
	});
}
