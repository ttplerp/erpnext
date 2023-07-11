// frappe.listview_settings['Vehicle Request'] = {
// add_fields: ["r_status", "operator", "employee"],        
// }

frappe.listview_settings['Vehicle Request'] = {
	add_fields: ["r_status","operator","employee"],
	get_indicator: function(doc) {

	},
};

// frappe.listview_settings['AMC Work Order'] = {
// 	add_fields: ["name", "direct_payment","payment_status"],
// 	get_indicator: function(doc) {
// 		console.log(doc.payment_status)
//         if(doc.direct_payment || doc.payment_status){
//             if(doc.payment_status=="Pending Payment") {
//                 return [__("Pending Payment"), "orange", "payment_status,=,Pending Payment"];
//             } else if (doc.payment_status=="Paid") {
//                 return [__("Paid"), "green", "payment_status,=,Paid"];
//             }if (doc.payment_status=="Payment Cancelled") {
//                 return [__("Payment Cancelled"), "red", "payment_status,=,Payment Cancelled"];
//             } 
//         }
// 	},
// };