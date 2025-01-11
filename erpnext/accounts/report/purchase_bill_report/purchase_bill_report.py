# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    validate_filters(filters)
    data = get_data(filters)
    columns = get_columns(filters)
    return columns, data

def validate_filters(filters):
    if filters.from_date and filters.to_date:
        if filters.from_date > filters.to_date:
            frappe.throw(_("The 'From Date' cannot be greater than the 'To Date'."))

def get_data(filters):
    cond = "WHERE docstatus = 1"
    params = []

    # Add filters to the condition
    if filters.branch:
        cond += " AND branch = %s"
        params.append(filters.branch)
    if filters.supplier:
        cond += " AND supplier = %s"
        params.append(filters.supplier)
    if filters.from_date and filters.to_date:
        cond += " AND posting_date BETWEEN %s AND %s"
        params.extend([filters.from_date, filters.to_date])
    if filters.bill_not_received:
        cond += " AND (bill_received IS NULL OR bill_received = '')"

    query = f"""
        SELECT name, branch, supplier, posting_date, grand_total, outstanding_amount, status, bill_received
        FROM `tabPurchase Invoice`
        {cond}
        ORDER BY posting_date ASC
    """
    invoices = frappe.db.sql(query, tuple(params), as_dict=True)

    data = [
        {
            "name": inv.name,
            "branch": inv.branch,
            "supplier": inv.supplier,
            "posting_date": inv.posting_date,
            "grand_total": inv.grand_total,
            "outstanding_amount": inv.outstanding_amount,
            "status": inv.status,
            "billed_received": "Yes" if inv.bill_received else "",
        }
        for inv in invoices
    ]
    return data

def get_columns(filters):
    return [
        {"fieldtype": "Link", "fieldname": "branch", "label": _("Branch"), "options": "Branch", "width": 200},
        {"fieldtype": "Link", "fieldname": "name", "label": _("Purchase Invoice"), "options": "Purchase Invoice", "width": 140},
        {"fieldtype": "Date", "fieldname": "posting_date", "label": _("Posting Date"), "width": 120},
        {"fieldtype": "Link", "fieldname": "supplier", "label": _("Supplier"), "options": "Supplier", "width": 180},
        {"fieldtype": "Currency", "fieldname": "grand_total", "label": _("Grand Total"), "width": 120},
        {"fieldtype": "Currency", "fieldname": "outstanding_amount", "label": _("Outstanding Amount"), "width": 120},
        {"fieldtype": "Data", "fieldname": "billed_received", "label": _("Bill Received"), "width": 120},
        {"fieldtype": "Data", "fieldname": "status", "label": _("Status"), "width": 100},
    ]
