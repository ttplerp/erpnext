frappe.ready(function() {
	frappe.web_form.fields_dict.country.set_data(["Bhutan"]);
	frappe.call({
		method: "erpnext.custom_filters.get_type_of_events",
		callback: function(response) {
			let types = response.message || [];
			let formated_opts = types.map(d => ({
				value: d.name
			}));
			frappe.web_form.fields_dict.event.set_data(formated_opts);
		}
	}) 

    frappe.web_form.on('event', (field, value) => {
	    console.log("Logging..." + value)
	frappe.call({
		method: "erpnext.custom_filters.get_category",
		args: {
			type_of_event: value,
		},
		callback: function(response) {
			let events = response.message || [];
			let formated_opts = events.map(d => ({
				value: d.name
			}));
			frappe.web_form.fields_dict.category.set_data(formated_opts);
		}
	})
    })

    frappe.web_form.on('country', (field, value) => {
	frappe.call({
		method: "erpnext.custom_filters.get_dzongkhags",
		args: {
			country: value || "Bhutan",
		},
		callback: function(response) {
			let dzo = response.message || [];
			let formated_opts = dzo.map(d => ({
				value: d.name
			}));
			frappe.web_form.fields_dict.dzongkhag.set_data(formated_opts);
		}
	})
    })

    frappe.web_form.on('dzongkhag', (field, value) => {
	frappe.call({
		method: "erpnext.custom_filters.get_gewogs",
		args: {
			dzongkhag: value,
		},
		callback: function(response) {
			let geo = response.message || [];
			let formated_opts = geo.map(d => ({
				value: d.name
			}));
			frappe.web_form.fields_dict.gewog.set_data(formated_opts);
		}
	})
    })
})

