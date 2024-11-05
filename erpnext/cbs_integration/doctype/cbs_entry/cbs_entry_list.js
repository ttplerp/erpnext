frappe.listview_settings['CBS Entry'] = {
	add_fields: ["docstatus", "status", "cbs_status"],
	get_indicator: function(doc) {
		var precision = frappe.defaults.get_default("float_precision");
		if (doc.docstatus == 0) {
            if(doc.status == "Pending"){
                return [__("Pending"), "orange", "status,=,Pending"];
            }
		} else if (doc.docstatus == 1) {
            if(doc.cbs_status=="SUCCESS"){
                return [__("Submitted"), "green", "cbs_status,=,SUCCESS"];
            }
            else if(doc.cbs_status == "FAILURE"){
                return [__("Failed"), "red", "cbs_status,=,FAILED"];
            }
		} else if (doc.status == "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		}
	}
};
