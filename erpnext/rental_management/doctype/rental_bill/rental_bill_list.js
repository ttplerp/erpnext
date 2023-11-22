frappe.listview_settings['Rental Bill'] = {
    add_fields: ["name", "yearmonth", "property_management_amount", "rent_amount", "received_amount", "discount_amount", "docstatus", "tds_amount", "adjusted_amount", "receivable_amount", "rent_write_off_amount", "outstanding_amount"],
    get_indicator: function (doc) {
            if (doc.adjusted_amount > 0 && (doc.outstanding_amount == 0 || doc.received_amount == 0)) {
                    return ["Adjusted", "blue"];
            }
            else if (doc.receivable_amount == doc.rent_write_off_amount && doc.adjusted_amount == 0){
                    return ["Written-off", "purple"];
            }
            else if (doc.receivable_amount == (doc.received_amount + doc.discount_amount + doc.tds_amount + doc.adjusted_amount)) {
                    return ["Received", "green"];
            }
            else if (doc.receivable_amount > (doc.received_amount + doc.discount_amount + doc.tds_amount + doc.adjusted_amount) && doc.received_amount > 0) {
                    return ["Partial Received", "yellow"];
            }
            else{
                    return ["Not Received", "orange"];
            }
    }
};