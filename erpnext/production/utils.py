# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    add_days,
    add_years,
    cstr,
    flt,
    format_datetime,
    formatdate,
    get_datetime,
    get_link_to_form,
    getdate,
    nowdate,
    today,
)

import erpnext
from erpnext import get_company_currency
from erpnext.setup.doctype.employee.employee import (
    InactiveEmployeeStatusError,
    get_holiday_list_for_employee,
)


@frappe.whitelist()
def submit_productions():
    for prd in frappe.db.sql("""
                             select name from `tabProduction` where
                             auto_submit = 1 and docstatus = 0
                             """, as_dict=1):
        doc = frappe.get_doc("Production", prd.name)
        if not frappe.db.exists("GL Entry", {"voucher_no": prd.name}):
            try:
                doc.submit()
                print("Submitted {}".format(doc.name))
            except Exception as e:
                print("Could not submit {}. Details: {}".format(doc.name, e))