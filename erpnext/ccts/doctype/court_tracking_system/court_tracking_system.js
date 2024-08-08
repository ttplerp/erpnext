// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Court Tracking System', {
	refresh: function (frm) {

		if (frm.doc.case_type == "Counter Litigation") {
			frm.toggle_reqd(["current_status", "investigation", "issue_details", "hearing_details"], 0);
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by",
				"loan_account_no", "guarantor", "sanction_date", "sanction_amount",
				"loan_product", "loan_category", "loan_tenure", "overdue_date", "loan_outstanding",
				"collateral_type", "exposure", "hearing_details"], 0);
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by", "issue_details"], 1);
		} else if (frm.doc.case_type == "NPL Recovery Cases") {
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by", "issue_details"], 0);
			frm.toggle_reqd(["current_status", "investigation", "issue_details", "hearing_details"], 0);

			frm.toggle_reqd(["cid_license_number", "borrower_filed_by",
				"loan_account_no", "guarantor", "sanction_date", "sanction_amount",
				"loan_product", "loan_category","loan_tenure", "overdue_date", "loan_outstanding",
				"collateral_type", "exposure", "hearing_details"], 1);
					
		} else if (frm.doc.case_type == "Criminal & ACC Cases") { 
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by", "issue_details"], 0);
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by",
				"loan_account_no", "guarantor", "sanction_date", "sanction_amount",
				"loan_product", "loan_category","loan_tenure", "overdue_date", "loan_outstanding",
				"collateral_type", "exposure", "hearing_details"], 0);
			frm.toggle_reqd(["current_status", "investigation", "issue_details", "hearing_details"], 1);
		}
	},
	onload: function(frm) {
		frm.set_query('loan_category', function() {
			return {
				filters: {
					"is_group": 1,
					"parent_product": "",
				}
			};
		});

		frm.set_query('loan_sub_category', function() {
			return {
				filters: {
					"is_sub_group": 1,
					"parent_product": frm.doc.loan_category,
				}
			};
		});
		
		frm.set_query("loan_product", function() {
			return {
				query: "erpnext.ccts.doctype.court_tracking_system.court_tracking_system.get_loan_product",
				filters: frm.doc.loan_sub_category ?
            			{"parent_product": frm.doc.loan_sub_category } : {"parent_product": frm.doc.loan_category}
			};
		});
	},
	case_type: function (frm) { 
		if (frm.doc.case_type == "Counter Litigation") {
			frm.toggle_reqd(["current_status", "investigation", "issue_details", "hearing_details"], 0);
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by",
				"loan_account_no", "guarantor", "sanction_date", "sanction_amount",
				"loan_product", "loan_category","loan_tenure", "overdue_date", "loan_outstanding",
				"collateral_type", "exposure", "hearing_details"], 0);
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by", "issue_details"], 1);
		} else if (frm.doc.case_type == "NPL Recovery Cases") {
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by", "issue_details"], 0);
			frm.toggle_reqd(["current_status", "investigation", "issue_details", "hearing_details"], 0);

			frm.toggle_reqd(["cid_license_number", "borrower_filed_by",
				"loan_account_no", "guarantor", "sanction_date", "sanction_amount",
				"loan_product", "loan_category", "loan_tenure", "overdue_date", "loan_outstanding",
				"collateral_type", "exposure", "hearing_details"], 1);
					
		} else if (frm.doc.case_type == "Criminal & ACC Cases") { 
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by", "issue_details"], 0);
			frm.toggle_reqd(["cid_license_number", "borrower_filed_by",
				"loan_account_no", "guarantor", "sanction_date", "sanction_amount",
				"loan_product", "loan_category", "loan_tenure", "overdue_date", "loan_outstanding",
				"collateral_type", "exposure", "hearing_details"], 0);
			frm.toggle_reqd(["current_status", "investigation", "issue_details", "hearing_details"], 1);
		}
	}
});
