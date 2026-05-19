from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe import msgprint
from frappe.utils import today, now, flt, cint, nowdate, getdate, formatdate, add_to_date

@frappe.whitelist(allow_guest=True)
def get_dzongkhags(country):
    if not country:
        frappe.throw("Country is required")
    return frappe.db.sql("select name from tabDzongkhags where country_name = %(country)s and disabled = 0", {"country": country}, as_dict=1)

@frappe.whitelist(allow_guest=True)
def get_gewogs(dzongkhag):
    if not dzongkhag:
        frappe.throw("Dzongkhag is required")
    return frappe.db.sql("select name from tabGewogs where dzongkhag = %(dzongkhag)s and disabled = 0", {"dzongkhag": dzongkhag}, as_dict=1)

@frappe.whitelist(allow_guest=True)
def get_type_of_events():
    return frappe.db.sql("select name from `tabType of Event` where disabled = 0", as_dict=1)


@frappe.whitelist(allow_guest=True)
def get_category(type_of_event):
    if not type_of_event:
        frappe.throw("Event Type is required")
    return frappe.db.sql("select name from `tabCategory of Deployment` where type_of_event = %(type_of_event)s and disabled = 0", {"type_of_event": type_of_event}, as_dict=1)
