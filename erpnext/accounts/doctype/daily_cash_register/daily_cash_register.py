# Copyright (c) 2025, Frappe Technologies Pvt. Ltd.
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, get_datetime
from frappe.model.document import Document

class DailyCashRegister(Document):
    pass

@frappe.whitelist()
def get_last_transaction_date(cash_account):
    """
    Retrieves the last transaction date and sets transaction_count = 1
    if a transaction exists for the given cash account in the Daily Cash Register.
    """
    last_entry = frappe.db.sql("""
        SELECT date
        FROM `tabDaily Cash Register`
        WHERE cash_account = %s AND docstatus = 1
        ORDER BY date DESC
        LIMIT 1
    """, (cash_account,), as_dict=True)
    
    last_date = last_entry[0].date if last_entry else None
    return {
        'message': last_date,
    }


@frappe.whitelist()
def is_cash_closed(cash_account, last_closed_on, date):
    """
    Checks if the cash has already been closed for the given date and cash account.
    """
    exists = frappe.db.exists('Daily Cash Register', {
        'cash_account': cash_account,
        'date': date,
        'docstatus': 1
    })
    return bool(exists)

@frappe.whitelist()
def fetch_gl_entries(cash_account = None, last_closed_on = None, date = None):
    """
    Fetches GL entries between the last closed date and the selected date for the given cash account.
    Returns separate lists for cash in and cash out entries, along with a summary.
    """
    if not (cash_account and last_closed_on and date):
        frappe.throw(_("Missing required parameters: Cash Account or Last Colsed On or Date"))

    entries = frappe.db.sql("""
        SELECT posting_date, voucher_type, voucher_no, debit, credit, remarks
        FROM `tabGL Entry`
        WHERE account = %s
          AND posting_date > %s
          AND posting_date <= %s
          AND docstatus = 1
        ORDER BY posting_date ASC
    """, (cash_account, last_closed_on, date), as_dict=True)

    cash_in_entries = []
    cash_out_entries = []
    total_cash_in = 0.0
    total_cash_out = 0.0

    for entry in entries:
        if flt(entry.debit) > 0:
            cash_in_entries.append(entry)
            total_cash_in += flt(entry.debit)
        elif flt(entry.credit) > 0:
            cash_out_entries.append(entry)
            total_cash_out += flt(entry.credit)

    # Calculate the opening balance as of the last closed date
    opening_balance = frappe.db.sql("""
        SELECT SUM(debit) - SUM(credit) AS balance
        FROM `tabGL Entry`
        WHERE account = %s
          AND posting_date <= %s
          AND docstatus = 1
    """, (cash_account, last_closed_on), as_dict=True)

    closing_balance = flt(opening_balance[0].balance) + total_cash_in - total_cash_out if opening_balance else 0.0

    return {
        'cash_in_entries': cash_in_entries,
        'cash_out_entries': cash_out_entries,
        'summary': {
            'total_cash_in': total_cash_in,
            'total_cash_out': total_cash_out,
            'closing_balance': closing_balance
        }
    }
