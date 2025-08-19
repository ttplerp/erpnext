// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Company Compact', {
	// onload_post_render: function(frm) {
	// 	if(frm.doc.type == "Company"){
	// 		console.log(frm.doc.type)
	// 		$('[data-fieldname="financial"] label.control-label').text("Hello");
	// 	}
	// 	$(".form-grid").each(function() {
	// 		// Get all child nodes, filter only text nodes
	// 		var textNode = $(this).contents().filter(function() {
	// 			return this.nodeType === Node.TEXT_NODE && this.textContent.trim() !== "";
	// 		})[0];
		
	// 		// if (textNode && textNode.textContent.trim() === "1. Financial") {
	// 		if (textNode) {
	// 			textNode.textContent = "1. Marketing ";
	// 		}
	// 	});
	// },
    // refresh(frm) {
    //     // Change df so future refreshes know about it
	// 	if(frm.doc.type != "Company"){
	// 		frm.fields_dict['financial'].df.label = "New Label Text";
			
	// 		// Change in DOM immediately
	// 		$(frm.fields_dict['financial'].wrapper)
	// 			.find('label.control-label')
	// 			.text("New Label Text");
	// 	}
    // }
    refresh(frm) {
        // Get the new value from the category field

        // Build the new label text
        let new_label_1 = ``;
        let new_label_2 = ``;
        let new_label_3 = ``;
        if(frm.doc.type == "Company"){
            new_label_1 = `2.1 Customer Perspective`;
            new_label_2 = `2.2 Innovation and Talent`;
            new_label_3 = `2.3 Risk and Control`;
        }

        // Update definition so Frappe knows about the change
        frm.fields_dict['non_financial_one'].df.label = new_label_1;
        frm.fields_dict['non_financial_two'].df.label = new_label_2;
        frm.fields_dict['non_financial_three'].df.label = new_label_3;

        // Update the visible DOM now
        $(frm.fields_dict['non_financial_one'].wrapper)
            .find('label.control-label')
            .text(new_label_1);
        // Update the visible DOM now
        $(frm.fields_dict['non_financial_two'].wrapper)
            .find('label.control-label')
            .text(new_label_2);
        // Update the visible DOM now
        $(frm.fields_dict['non_financial_three'].wrapper)
            .find('label.control-label')
            .text(new_label_3);
        },
    type(frm) {
        // Get the new value from the category field

        // Build the new label text
        let new_label_1 = ``;
        if(frm.doc.type == "Company"){
            new_label_1 = `2.1 Customer Perspective`;
        }

        // Update definition so Frappe knows about the change
        frm.fields_dict['non_financial_one'].df.label = new_label_1;

        // Update the visible DOM now
        $(frm.fields_dict['non_financial_one'].wrapper)
            .find('label.control-label')
            .text(new_label_1);
    }
});
