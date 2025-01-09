# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr

def execute(filters=None):
    validate_filters(filters)
    columns = get_columns()
    queries = construct_query(filters)
    data = get_data(queries, filters)

    return columns, data

def get_data(query, filters=None):
    data = []
    if filters.issued_to:
        datas = frappe.db.sql(query, (filters.from_date, filters.to_date, filters.issued_to), as_dict=True)
    else:
        datas = frappe.db.sql(query, (filters.from_date, filters.to_date), as_dict=True)
    
    for d in datas:
        # row = [
        #     d.entry_date, d.item_code, d.item_name, d.brand, d.qty, 
        #     d.issued_to, d.custodian, d.issued_date, d.amount, 
        #     d.location, d.asset_category, d.asset_station
        # ]
        data.append({
            "asset_issue_id": d.asset_issue_id,
            "entry_date": d.entry_date,
            "item_code": d.item_code,
            "item_name": d.item_name,
            "qty": d.qty,
            "amount": d.amount,
            "asset_category": d.asset_category,
            "asset_sub_category": d.asset_sub_category,
            "issued_to": d.issued_to,
            "custodian": d.custodian,
            "brand": d.brand,
            "issued_date": d.issued_date,
            "asset_station": d.asset_station,
        })
    return data

def construct_query(filters=None):
    query = """
            select id.name as asset_issue_id,id.entry_date, id.item_code, id.item_name, id.qty, id.brand,
			id.issued_to, id.employee_name as custodian, 
			id.issued_date, id.amount, id.location, id.asset_category, id.asset_sub_category, id.asset_station 
            from `tabAsset Issue Details` as id 
			INNER JOIN `tabItem` i ON id.item_code = i.name
            where id.docstatus = 1 and id.entry_date between %s and %s """

    if filters.issued_to:
        query += "and id.issued_to = %s "

    query += "order by id.creation asc"

    return query

def validate_filters(filters):
    if not filters.fiscal_year:
        frappe.throw(_("Fiscal Year {0} is required").format(
            filters.fiscal_year))

    fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, [
                                      "year_start_date", "year_end_date"], as_dict=True)
    if not fiscal_year:
        frappe.throw(_("Fiscal Year {0} does not exist").format(
            filters.fiscal_year))
    else:
        filters.year_start_date = getdate(fiscal_year.year_start_date)
        filters.year_end_date = getdate(fiscal_year.year_end_date)

    if not filters.from_date:
        filters.from_date = filters.year_start_date

    if not filters.to_date:
        filters.to_date = filters.year_end_date

    filters.from_date = getdate(filters.from_date)
    filters.to_date = getdate(filters.to_date)

    if filters.from_date > filters.to_date:
        frappe.throw(_("From Date cannot be greater than To Date"))

    # if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
    #     frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")
    #                     .format(formatdate(filters.year_start_date)))

    #     filters.from_date = filters.year_start_date

    # if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
    #     frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")
    #                     .format(formatdate(filters.year_end_date)))
    #     filters.to_date = filters.year_end_date

def get_columns():
    return [
        {
            "fieldname": "asset_issue_id",
            "label": "Issued ID",
            "fieldtype": "Link",
            "options": "Asset Issue Details",
            "width": 130
        },
        {
            "fieldname": "entry_date",
            "label": "Entry Date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "fieldname": "item_code",
            "label": "Material Code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 130
        },
        {
            "fieldname": "item_name",
            "label": "Material Name",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "fieldname": "qty",
            "label": "Quantity",
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "amount",
            "label": "Gross Amount (Nu.)",
            "fieldtype": "Float",
            "width": 150
        },
        {
            "fieldname": "asset_category",
            "label": "Asset Category",
            "fieldtype": "data",
            "width": 150
        },
        {
            "fieldname": "asset_sub_category",
            "label": "Asset Sub Category",
            "fieldtype": "data",
            "width": 150
        },
        {
            "fieldname": "issued_to",
            "label": "Custodian",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 110
        },
        {
            "fieldname": "custodian",
            "label": "Custodian Name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "issued_date",
            "label": "Issued Date",
            "fieldtype": "Date",
            "width": 110
        },
        {
            "fieldname": "location",
            "label": "Location",
            "fieldtype": "data",
            "width": 120
        },
         {
            "fieldname": "brand",
            "label": "Brand",
            "fieldtype": "Data",
            "width": 100
        },
        
        {
            "fieldname": "asset_station",
            "label": "Asset Station",
            "fieldtype": "Link",
            "options": "Asset Station",
            "width": 150
        },
    ]
