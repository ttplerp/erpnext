frappe.listview_settings['Online Order'] = {
    get_indicator: function(doc) {
	if (doc.status === "Ordered") {
	    return [__("Ordered"), "orange", "status,=,Ordered"];
	} else if (doc.status === "Payment verified") {
	    return [__("Payment verified"), "grey", "status,=,Payment verified"];
	} else if (doc.status === "Ready for pickup") {
	    return [__("Ready for pickup"), "blue", "status,=,Ready for pickup"];
	} else if (doc.status === "Delivered") {
	    return [__("Delivered"), "green", "status,=,Delivered"];
	}
    }
};

