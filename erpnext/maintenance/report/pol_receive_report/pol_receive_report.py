# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
def execute(filters=None):
        columns = get_columns()
        data = get_data(filters)
        return columns, data
    
def get_columns():
    return [
        {
            "fieldname":"name",
            "label":_("Reference"),
            "fieldtype":"Link",
            "options":"POL",
            "width":120
        },
        {
            "fieldname":"equipment_number",
            "label":_("Equipment No."),
            "fieldtype":"Link",
            "options":"Equipment",
            "width":120
        },
        {
            "fieldname":"book_type",
            "label":_("Book Type"),
            "fieldtype":"Data",
            "width":100
        },
        {
            "fieldname":"fuelbook",
            "label":_("Fuelbook"),
            "fieldtype":"Data",
            "width":100
        },
        {
            "fieldname":"supplier",
            "label":_("Supplier"),
            "fieldtype":"Link",
            "options":"Supplier",
            "width":200
        },
        {
            "fieldname":"item_name",
            "label":_("Item Name"),
            "fieldtype":"Link",
            "options":"Item",
            "width":150
        },
        {
            "fieldname":"posting_date",
            "label":_("Posting Date"),
            "fieldtype":"Date",
            "width":150
        },
        {
            "fieldname":"current_km_reading",
            "label":_("Current KM Reading"),
            "fieldtype":"Float",
            "width":150
        },
        {
            "fieldname":"km_difference",
            "label":_("KM Difference"),
            "fieldtype":"Float",
            "width":120
        },
        {
            "fieldname":"mileage",
            "label":_("Mileage"),
            "fieldtype":"Float",
            "width":100
        },
        {
            "fieldname":"qty",
            "label":_("Qty"),
            "fieldtype":"Float",
            "width":60
        },
        {
            "fieldname":"rate",
            "label":_("Rate"),
            "fieldtype":"Currency",
            "width":100
        },
        {
            "fieldname":"od_amount",
            "label":_("OD Amount"),
            "fieldtype":"Currency",
            "width":130
        },
        {
            "fieldname":"total_amount",
            "label":_("Payable Amount"),
            "fieldtype":"Currency",
            "width":130
        },
        {
            "fieldname":"book_balance",
            "label":_("Book Value"),
            "fieldtype":"Currency",
            "width":120
        }
    ]


def get_data(filters):
    query = """
            SELECT
                p.name,
                p.equipment_number,
                p.book_type,
                p.fuelbook,
                p.supplier,
                p.item_name,
                p.posting_date,
                p.current_km_reading,
                p.km_difference,
                p.mileage,
                p.qty,
                p.rate,
                p.od_amount,
                COALESCE(p.total_amount, 0) as total_amount,
                (select sum(balance) from `tabPOL Advance Item` where parent = p.name) as book_balance
            FROM
                `tabPOL` as p
            WHERE p.docstatus = 1 
    """

    if filters.get("branch"):
        query += " and p.branch = '{}'".format(filters.branch) 

    if filters.get("from_date") and filters.get("to_date"):
        query += " and p.posting_date between '{}' and '{}'".format(filters.from_date,filters.to_date)

    if filters.get("direct"):
        query += " and p.direct_consumption = 1"
    else:
        query += " and p.direct_consumption =  0"
    if filters.equipment:
        query += " and p.equipment='{}'".format(filters.equipment)

    return frappe.db.sql(query)

    
@frappe.whitelist()
# this method will fetch the previous km reading to show in print format
def get_previous_km(from_date,branch,equipment,direct_consumption):
    query = """
            SELECT
                current_km_reading
            FROM
                `tabPOL`
            WHERE docstatus = 1 
            AND posting_date < '{}'
        """.format(from_date)
    
    if branch:
        query += " and branch = '{}'".format(branch) 
    if direct_consumption:
        query += " and direct_consumption = 1"
    else:
        query += " and direct_consumption =  0"
    if equipment:
        query += " and equipment='{}'".format(equipment)
    query += " order by posting_date desc limit 1 "
    data = frappe.db.sql(query,as_dict=True)
    if not data:
        cur_km_reading = 0
    else:
        cur_km_reading = data[0].cur_km_reading
    return cur_km_reading