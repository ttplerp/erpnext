# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "parent_account",
            "label": "Parent Account",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "account",
            "label": "Account",
            "fieldtype": "Data",
            "width": 160
        },
        {
            "fieldname": "total_draft",
            "label": "Total Draft",
            "fieldtype": "Data",
            "width": 200
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    group = 'a.parent_account'
    if filters and filters.get("account_wise"):
        group = 'a.name'
    query = '''
        SELECT
            a.parent_account AS parent_account,
            a.name AS account,
            SUM(gl.credit - gl.debit) AS total_draft
        FROM
            `tabGL Entry` AS gl
        INNER JOIN
            `tabAccount` AS a ON gl.account = a.name
        WHERE
            gl.company = "VAJRA BUILDERS PRIVATE LIMITED"
            AND a.parent_account IN ("21.200 - Bank Overdraft", "22.100 - Unsecured Loans", "22.200 - Secured Loans (Bank)")
            {conditions}
        GROUP BY
            {group}
    '''.format(conditions=conditions,group=group)
    data = frappe.db.sql(query, as_dict=1)
    return data

def get_conditions(filters):
    conditions = []
    if filters and filters.get("parent_account"):
        conditions.append("a.parent_account = '{}'".format(filters.get("parent_account")))
    if filters and filters.get("account"):
        conditions.append("a.name = '{}'".format(filters.get("account")))
    if filters and filters.get("fiscal_year"):
        conditions.append("fiscal_year = '{}'".format(filters.get("fiscal_year")))
    if filters.get("monthly"):
        conditions.append("MONTH(gl.posting_date) = '{}'".format(filters.get("monthly")))

    return "AND {}".format(" AND ".join(conditions)) if conditions else ""
