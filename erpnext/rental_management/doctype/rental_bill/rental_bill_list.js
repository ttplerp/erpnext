frappe.listview_settings['Rental Bill'] = {
    add_fields: ["name", "yearmonth", "property_management_amount", "rent_amount", "received_amount", "discount_amount", "docstatus", "tds_amount", "adjusted_amount", "receivable_amount", "rent_write_off_amount"],
    get_indicator: function (doc) {
            if (doc.rent_amount + doc.property_management_amount == doc.adjusted_amount) {
                    return ["Adjusted", "blue"];
            }
            else if (doc.receivable_amount == doc.rent_write_off_amount){
                    return ["Written-off", "purple"];
            }
            else if (doc.receivable_amount == (doc.received_amount + doc.discount_amount + doc.tds_amount + doc.adjusted_amount + doc.property_management_amount)) {
                    return ["Received", "green"];
            }
            else if (doc.receivable_amount > (doc.received_amount + doc.discount_amount + doc.tds_amount + doc.property_management_amount) && doc.received_amount > 0) {
                    return ["Partial Received", "yellow"];
            }
            else{
                    return ["Not Received", "orange"];
            }
    }
};