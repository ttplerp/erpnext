// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Loan Products', {
	// refresh: function(frm) {

	// }
	onload: function(frm) {
		
		frm.set_query("parent_product", function() {
			return {
				query: "erpnext.ccts.doctype.loan_products.loan_products.get_loan_product"
			};
		});
	},
});
