# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr

def execute(filters=None):
    validate_filters(filters)
    columns = get_columns(filters)
    queries = construct_query(filters)
    data = get_data(queries, filters)

    return columns, data

def get_data(query, filters):
    data = []
    datas = frappe.db.sql(query, as_dict=True)
    ini = su = cm = co = ad = av = cur = 0
    condition = ""
    if filters.business_activity:
        condition += " and business_activity = '{0}'".format(filters.business_activity)
    
    if filters.voucher_no:
        condition += " and reference_no = '{0}'".format(filters.voucher_no)

    for d in datas:
        query = """ SELECT 
                        com_ref, account, 
                        (select a.account_number from `tabAccount` a where a.name = b.account) as account_number, 
                        reference_date, cost_center, name, amount, reference_type, reference_no, item_code, 
                        (select a.amount from `tabCommitted Budget` a where b.com_ref=a.name) as committed, 
                        consumed_cost_center
                    FROM `tabConsumed Budget` b
                    WHERE account = '{account}' 
                    and reference_date BETWEEN '{start_date}' and '{end_date}'
                    and cost_center = "{cost_center}"
                    {condition}
                    order by reference_date Desc
                """.format(account=d.account, start_date=filters.from_date, 
                end_date=filters.to_date, cost_center=d.cost_center, condition=condition)
        ini+=flt(d.initial_budget)
        su+=flt(d.supplement)

        query = frappe.db.sql(query, as_dict=True)
        for a in query:
            if not a.committed:
                    a.committed = 0
            if not a.amount:
                a.amount = 0
                
            adjustment = flt(d.added) - flt(d.deducted)
            supplement = flt(d.supplement)
            
            if a.committed > 0:
                a.committed -= a.amount
                if a.committed < 0:
                    a.committed = 0
            available = flt(d.initial_budget) + flt(adjustment) + flt(d.supplement) - flt(a.amount) - flt(a.committed)
            current   = flt(d.initial_budget) + flt(d.supplement) +flt(d.adjustment)

            row = {
                "date": a.reference_date,
                "account": a.account,
                "account_number": a.account_number,
                "cost_center": a.cost_center,
                "consumed_cost_center": a.consumed_cost_center,
                "initial": flt(d.initial_budget),
                "supplementary": supplement,
                "adjustment": adjustment,
                "current": current,
                "committed": a.committed,
                "consumed": a.amount,
                "available": available,
                "reference_type": a.reference_type,
                "reference_no": a.reference_no
            }

            data.append(row)
            cm+=a.committed
            co+=a.amount
            ad+=adjustment
    row = {
        "date":"",
        "project": "Total",
        "initial": ini,
        "supplementary": su,
        "adjustment": ad,
        "current":flt(ini)+flt(ad)+flt(su),
        "committed": cm,
        "consumed": co,
        "available": flt(ini) + flt(ad) + flt(su) - flt(co) - flt(cm)
    }
    data.insert(0, row)
    return data

def construct_query(filters=None):
    query = """
            select 
                b.cost_center, ba.account, (select a.account_number from `tabAccount` a where a.name = ba.account) as account_number, ba.budget_type,
                ba.initial_budget as initial_budget, 
                ba.budget_received as added, 
                ba.budget_sent as deducted, 
                ba.supplementary_budget as supplement
            from `tabBudget` b, `tabBudget Account` ba 
            where b.docstatus = 1 and b.name = ba.parent
            and ba.initial_budget != 0 and b.fiscal_year = \'""" + str(filters.fiscal_year) + "\' "
            
    if filters.cost_center:
        lft, rgt = frappe.db.get_value("Cost Center", filters.cost_center, ["lft", "rgt"])
        query += """ and (b.cost_center in (select a.name 
                                        from `tabCost Center` a 
                                        where a.lft >= {1} and a.rgt <= {2}
                                        ) 
                    or b.cost_center = '{0}')
            """.format(filters.cost_center, lft, rgt)

    if filters.account:
        query += " and ba.account = \'" + str(filters.account) + "\' "

    if filters.business_activity:
        query += " and b.business_activity = \'" + str(filters.business_activity) + "\' "
    return query

def validate_filters(filters):
    if not filters.fiscal_year:
        frappe.throw(_("Fiscal Year {0} is required").format(filters.fiscal_year))

    fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
    if not fiscal_year:
        frappe.throw(_("Fiscal Year {0} does not exist").format(filters.fiscal_year))
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

    if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
        frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")\
            .format(formatdate(filters.year_start_date)))

        filters.from_date = filters.year_start_date

    if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
        frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")\
            .format(formatdate(filters.year_end_date)))
        filters.to_date = filters.year_end_date


def get_columns(filters):
    return [
        {
            "fieldname": "date",
            "label": "Reference Date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "account",
            "label": "Account Head",
            "fieldtype": "Link",
            "options": "Account",
            "width": 190
        },
        {
            "fieldname": "cost_center",
            "label": "Budget Cost Center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 190
        },
        {
            "fieldname": "consumed_cost_center",
            "label": "Consumed Cost Center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 190
        },
        {
            "fieldname": "initial",
            "label": "Initial Budget",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "fieldname": "supplementary",
            "label": "Supplementary Budget",
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "adjustment",
            "label": "Budget Adjustment",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "current",
            "label": "Current Budget",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "committed",
            "label": "Committed Budget",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "consumed",
            "label": "Consumed Budget",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "available",
            "label": "Available Budget",
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "fieldname": "reference_type",
            "label": "Voucher Type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "reference_no",
            "label": "Voucher No",
            "fieldtype": "Dynamic Link",
            "options": "reference_type",
            "width": 120
        },
        {
            "fieldname": "item_code",
            "label": "Item Code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 80
        }
    ]
    