# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_column(filters), get_data(filters)
	return columns, data

def get_column(filters):
    columns = [
		("Case") + ":Link/Court Tracking System:150",
		("Case Type") + ":Data:200",
        ("Date") + ":Date:120",
        ("Branch") + ":Data:200",
        ("owner") + ":Link/User:200",

        ("CID/ License Number") + ":Data:150",
        ("Borrower/Filed By") + ":Data:150",
        ("Loan Account Number") + ":Data:150",
        ("Guarantor") + ":Data:150",
        ("Loan Product") + ":Data:150",
        ("Overdue Amount") + ":Data:150",
        ("Loan Outstanding") + ":Data:150",
        ("Collateral Type") + ":Data:150",

        ("Issue Details") + ":Data:150",
        ("Investigation") + ":Data:150",                
        ("Current Status") + ":Data:150", 
    ]
    # if filters.get("case_type") == "NPL Recovery Cases":
    #     columns.append([
    #         ("CID/ License Number") + ":Data:150",
	#         ("Borrower/Filed By") + ":Data:150",
    #         ("Loan Account Number") + ":Data:150",
    #         ("Guarantor") + ":Data:150",
    #         ("Loan Product") + ":Data:150",
    #         ("Overdue Amount") + ":Data:150",
    #         ("Loan Outstanding") + ":Data:150",
    #         ("Collateral Type") + ":Data:150",
    #     ])
    # if filters.get("case_type") == "Counter Litigation":
    #     columns.append([
    #         ("CID/ License Number") + ":Data:150",
	#         ("Borrower/Filed By") + ":Data:150",
    #     ])

    # if filters.get("case_type") == "Criminal & ACC Cases":
    #     columns.append([
    #         ("Issue Details") + ":Data:150",
	#         ("Investigation") + ":Data:150",                
    #         ("Current Status") + ":Data:150",         
    #     ])
    return columns
def get_condition(filters):
    conds = ""
    if filters.case_type:
        conds += "and case_type='{}'".format(filters.case_type)
    return conds

def get_data(filters):
    cond = get_condition(filters)
    return frappe.db.sql("""
		SELECT 
			name,
			case_type,
            date,
            branch,
            owner,
                                    
			cid_license_number, 
			borrower_filed_by,
			loan_account_no,
        
            guarantor,
            loan_product,
            overdue_amount,
            loan_outstanding,
            collateral_type,
            issue_details,
            investigation,
            current_status          
			
			
		FROM `tabCourt Tracking System` 
        WHERE docstatus = 1 {condition}
	""".format(condition=cond))

# WHERE docstatus = 1 {condition}
