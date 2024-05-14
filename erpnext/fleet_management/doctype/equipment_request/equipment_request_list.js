frappe.listview_settings['Equipment Request'] = {
    add_fields: ["docstatus", "ehf"],
    get_indicator: function(doc) {
        if(doc.ehf != null) {
            return ["EHF Created", "orange"];
        }else {
            return ["ER Created", "green"];
        }
    }
};
