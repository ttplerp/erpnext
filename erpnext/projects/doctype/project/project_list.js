frappe.listview_settings['Project'] = {
    add_fields: ["status"],
    get_indicator: function (doc) {
            if (doc.status == "Capitalized") {
                    return ["Capitalized", "green"];
            }
    }
};
