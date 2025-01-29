// JavaScript Function to Retrieve Applicant Information
function getApplicantInfo() {
    var cidInput = document.getElementsByName("cid")[0];
    var cidValue = parseInt(cidInput.value);

    if (!cidInput.checkValidity() || isNaN(cidValue) || cidValue.toString().length !== 11) {
        alert("Please enter a valid 11-digit CID (numeric only).");
        return;
    }
    frappe.call({
        method: "erpnext.www.check-status.index.get_applicant_info", // Replace with the actual method path
        args: {
            cid: cidValue
        },
        callback: function (r) {
            if (!r.message) {
                alert("Error: Unable to retrieve applicant information.");
                return;
            }
            console.log(r.message) 
            displayApplicantInfo(r.message);
        }
    });
}

function displayApplicantInfo(response) {
    var infoContainer = document.getElementById("applicant-info");

    if (response && response.applicant_info && response.applicant_info.length > 0) {
        var applicant = response.applicant_info[0]; // Access the first applicant in the array

        var tableHTML = '<table class="table table-bordered table-striped table-condensed table-custom-width">' +
            '<colgroup><col style="width: 50%;"><col style="width: 50%;"></colgroup>' +
            '<thead><tr><th colspan="2" class="table-heading-one">Applicant Information</th></tr></thead>' +
            '<tbody>' + 
            '<tr><td class="table-heading">CID</td><td>' + applicant.cid + '</td></tr>' +
            '<tr><td class="table-heading">Applicant Name</td><td>' + applicant.applicant_name + '</td></tr>' +
            '<tr><td class="table-heading">Employment Type</td><td>' + applicant.employment_type + '</td></tr>' +
            '<tr><td class="table-heading">Location</td><td>' + applicant.work_station + '</td></tr>' +
            '<tr><td class="table-heading">Applicant Rank</td><td>' + applicant.applicant_rank + '</td></tr>' +
            '<tr><td class="table-heading">Mobile No</td><td>' + applicant.mobile_no + '</td></tr>' +
            '<tr><td class="table-heading">Status</td><td>' + applicant.application_status + '</td></tr>' +
            '<tr><td class="table-heading">Building Classification</td><td>' + applicant.building_classification + '</td></tr>' +
            '<tr><td class="table-heading">Application Date & Time</td><td>' + applicant.application_date_time + '</td></tr>' +
           
            '</tbody></table>';

        infoContainer.innerHTML = tableHTML;
    } else {
        infoContainer.innerHTML = '<p>No Record found</p>';
    }
}

