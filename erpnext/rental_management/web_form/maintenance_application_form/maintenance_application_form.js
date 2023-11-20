// the code below dont check the repeat submission
// ---------------------------------------------------->
// frappe.ready(function() {

//     let typingTimer;
//     let timeoutDuration = 2000;
//     const inputField = document.querySelector('[data-fieldname="cidd"]');
  
//     inputField.addEventListener('keydown', function(event) {
//         clearTimeout(typingTimer);
  
//         typingTimer = setTimeout(() => {
//             const inputValue = inputField.value;
  
//             frappe.call({
//                 method: "erpnext.rental_management.doctype.maintenance_application_form.maintenance_application_form.get_cid_detail",
//                 args: {
//                     tenant_cid: frappe.web_form.get_value('cidd')
//                 },
//                 callback: function (response) {
//                     if (response && response.message && response.message.length > 0) {
//                         const tenantId = response.message[0].name;
//                         const tenantName = response.message[0].tenant_name;
//                         const blockNo = response.message[0].block_no;
//                         const flatNo = response.message[0].flat_no;
//                         const locationName = response.message[0].location_name;
//                         const dzongkhag = response.message[0].dzongkhag;
//                         const locations = response.message[0].locations;
//                         const phoneNo = response.message[0].phone_no;
//                         frappe.web_form.set_value('tenant_name', tenantName);
//                         frappe.web_form.set_value('block_no', blockNo );
//                         frappe.web_form.set_value('flat_no', flatNo);
//                         frappe.web_form.set_value('location_name', locationName);
//                         frappe.web_form.set_value('dzongkhag', dzongkhag);
//                         frappe.web_form.set_value('location', locations);
//                         frappe.web_form.set_value('mobile_no', phoneNo);
//                         frappe.web_form.set_value('tenant_id', tenantId);
                        
//                     } else {
//                         frappe.msgprint('No tenant name found');
//                     }
//                 },
//                 error: function (err) {
//                     frappe.msgprint('Error occurred: ' + err);
//                 }
//             });
//         }, timeoutDuration);
//     });
// });




//this code below checks if the same cid 
//------------------------------------------------------------------


// frappe.ready(function() {

//     let typingTimer;
//     let timeoutDuration = 2000;
//     const inputField = document.querySelector('[data-fieldname="cidd"]');
  
//     inputField.addEventListener('keydown', function(event) {
//         clearTimeout(typingTimer);
  
//         typingTimer = setTimeout(() => {
//             const inputValue = inputField.value;
  
//             frappe.call({
//                 method: "erpnext.rental_management.doctype.maintenance_application_form.maintenance_application_form.get_cid_detail",
//                 args: {
//                     tenant_cid: frappe.web_form.get_value('cidd')
//                 },
//                 callback: function (response) {
//                     if (response && response.message && response.message.length > 0) {
//                         const tenantId = response.message[0].name;
//                         const tenantName = response.message[0].tenant_name;
//                         const blockNo = response.message[0].block_no;
//                         const flatNo = response.message[0].flat_no;
//                         const locationName = response.message[0].location_name;
//                         const dzongkhag = response.message[0].dzongkhag;
//                         const locations = response.message[0].locations;
//                         const phoneNo = response.message[0].phone_no;
//                         frappe.web_form.set_value('tenant_name', tenantName);
//                         frappe.web_form.set_value('block_no', blockNo );
//                         frappe.web_form.set_value('flat_no', flatNo);
//                         frappe.web_form.set_value('location_name', locationName);
//                         frappe.web_form.set_value('dzongkhag', dzongkhag);
//                         frappe.web_form.set_value('location', locations);
//                         frappe.web_form.set_value('mobile_no', phoneNo);
//                         frappe.web_form.set_value('tenant_id', tenantId);
                        
//                     } else {
//                         frappe.msgprint('No tenant name found');
//                     }
//                 },
//                 error: function (err) {
//                     frappe.msgprint('Error occurred: ' + err);
//                 }
//             });
//         }, timeoutDuration);
//     });
// });


frappe.ready(function() {

    
   

    let typingTimer;
    let timeoutDuration = 2000;
    const inputField = document.querySelector('[data-fieldname="cidd"]');

    inputField.addEventListener('keydown', function(event) {
        clearTimeout(typingTimer);

        typingTimer = setTimeout(() => {
            const inputValue = frappe.web_form.get_value('cidd');

            frappe.call({
                method: "erpnext.rental_management.doctype.maintenance_application_form.maintenance_application_form.checkCidExistence",
                args: {
                    tenant_cid: inputValue
                },
                callback: function(response) {
                    if (response && response.message === true) {
                       
                        frappe.web_form.set_value('cidd', '');
                        frappe.web_form.set_value('tenant_name', '');
                        frappe.web_form.set_value('block_no', '');
                        frappe.web_form.set_value('flat_no', '');
                        frappe.web_form.set_value('location_name', '');
                        frappe.web_form.set_value('dzongkhag', '');
                        frappe.web_form.set_value('location', '');
                        frappe.web_form.set_value('mobile_no', '');
                        frappe.web_form.set_value('tenant_id', '');
                      
                    } else {
                        fetchCIDDetails(inputValue);
                    }
                },
                error: function(err) {
                    frappe.msgprint('Error occurred: ' + err);
                    
                }
            });
        }, timeoutDuration);
    });

    function fetchCIDDetails(cid) {
        frappe.call({
            method: "erpnext.rental_management.doctype.maintenance_application_form.maintenance_application_form.get_cid_detail",
            args: {
                tenant_cid: cid
            },
            callback: function(response) {
                if (response && response.message && response.message.length > 0) {
                    const tenantId = response.message[0].name;
                    const tenantName = response.message[0].tenant_name;
                    const blockNo = response.message[0].block_no;
                    const flatNo = response.message[0].flat_no;
                    const locationName = response.message[0].location_name;
                    const dzongkhag = response.message[0].dzongkhag;
                    const locations = response.message[0].locations;
                    const phoneNo = response.message[0].phone_no;
                    frappe.web_form.set_value('tenant_name', tenantName);
                    frappe.web_form.set_value('block_no', blockNo);
                    frappe.web_form.set_value('flat_no', flatNo);
                    frappe.web_form.set_value('location_name', locationName);
                    frappe.web_form.set_value('dzongkhag', dzongkhag);
                    frappe.web_form.set_value('location', locations);
                    frappe.web_form.set_value('mobile_no', phoneNo);
                    frappe.web_form.set_value('tenant_id', tenantId);
                } else {
                    frappe.web_form.set_value('cidd', '');
                    frappe.web_form.set_value('tenant_name', '');
                    frappe.web_form.set_value('block_no', '');
                    frappe.web_form.set_value('flat_no', '');
                    frappe.web_form.set_value('location_name', '');
                    frappe.web_form.set_value('dzongkhag', '');
                    frappe.web_form.set_value('location', '');
                    frappe.web_form.set_value('mobile_no', '');
                    frappe.web_form.set_value('tenant_id', '');
                    frappe.msgprint('No tenant name found');

                }
            },
            error: function(err) {
                frappe.msgprint('Error occurred: ' + err);
            }
        });
    }
});




