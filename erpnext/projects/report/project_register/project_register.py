# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint,add_days, cstr, flt, getdate, nowdate, rounded, date_diff

def execute(filters=None):
	columns = get_columns(filters)
	data    = get_data(filters)
	return columns, data

def get_columns(filters):
        if filters.get("additional_info"):
            cols = [
                    ("ID")                  + ":Link/Project:100",
                    ("Project")             + ":Data:250",
                    ("Customer")            + ":Link/Customer:120",
                    ("Physical Progress")   + ":Percent:120",
                    ("Status")              + ":Data:120",
                    ("Exp Start Date")      + ":Date:120",
                    ("Exp End Date")        + ":Date:120",
                    ("Advance")             + ":Currency:120",
                    ("Project Value (A)")   + ":Currency:120",
                    ("Price Adj (B)")       + ":Currency:120",
                    ("Advance Adj (C)")     + ":Currency:120",
                    ("TDS (D)")             + ":Currency:120",
                    ("Other Ded (E)")       + ":Currency:120",
                    ("Received (F)")        + ":Currency:120",
                    ("Balance(A+B-C-D-E-F)")+ ":Currency:150",
                    ("Branch")              + ":Link/Branch:120",
                    ("Cost Center")         + ":Link/Cost Center:120",
                    ("Created By")          + ":Data:120",
                    ("Created Date")        + ":Date:120",
                    ("Modified By")         + ":Data:120",
                    ("Modified Date")       + ":Date:120"
                ]
        else:
            cols = [
                    ("ID")                  + ":Link/Project:80",
                    ("Project")             + ":Data:250",
                    ("Customer")            + ":Link/Customer:120",
                    ("Physical Progress")   + ":Percent:120",
                    ("Status")              + ":Data:120",
                    ("Exp Start Date")      + ":Date:120",
                    ("Exp End Date")        + ":Date:120",
                    ("Project Value (A)")   + ":Currency:120",
                    ("Branch")              + ":Link/Branch:120",
                    ("Cost Center")         + ":Link/Cost Center:120"
                ]                

        return cols

def get_data(filters):
        cond  = get_conditions(filters)
        if filters.get("additional_info"):
            query = """
                    select name,
                            project_name,
                            customer,
                            percent_complete,
                            status,
                            project_name,
                            expected_start_date,
                            expected_end_date,
                            ifnull(boq_value,0) as project_value,
                            branch,
                            cost_center,
                            owner,
                            creation,
                            modified_by,
                            modified
                    from `tabProject` p
                    {0}
                    order by creation desc
            """.format(cond)
        else:
            query = """
                    select  name,
                            project_name,
                            customer,
                            percent_complete,
                            status,
                            expected_start_date,
                            expected_end_date,
                            ifnull(boq_value,0) as project_value,
                            branch,
                            cost_center
                    from `tabProject` p
                    {0}
                    order by creation desc
            """.format(cond)                

        if filters.get("additional_info"):
            data  = []
            result = frappe.db.sql(query, as_dict=1)
            
            for r in result:
                advance_amount   = 0.0
                advance_adjusted = 0.0
                price_adjustment = 0.0
                tds_amount       = 0.0
                other_ded        = 0.0
                payment_received = 0.0

                # advance_amount
                advance_amount, advance_adjusted = frappe.db.sql("""
                                        select
                                                sum(ifnull(received_amount,0)) as received_amount,
                                                sum(ifnull(adjustment_amount,0)) as adjustment_amount
                                        from  `tabProject Advance`
                                        where project   = "{0}"
                                        and   docstatus = 1
                                """.format(r.name))[0]

                # price_adjustment, tds_amount, other_ded, payment_received
                price_adjustment, tds_amount, other_ded, payment_received = frappe.db.sql("""
                    select
                        sum(ifnull(price_adjustment_amount,0)) as price_adjustment_amount,
                        sum(ifnull(tds_amount,0)) as tds_amount,
                        sum(ifnull(total_deduction_amount,0)) as other_ded,
                        sum(ifnull(net_amount-outstanding_amount,0)) as payment_received
                    from  `tabProject Invoice`
                    where project   = "{0}"
                    and   docstatus = 1
                        """.format(r.name))[0]
                data.append((
                        r.name,
                        r.project_name,
                        r.customer,
                        r.percent_complete,
                        r.status,
                        r.expected_start_date,
                        r.expected_end_date,
                        flt(advance_amount),
                        flt(r.project_value),
                        flt(price_adjustment),
                        flt(advance_adjusted),
                        flt(tds_amount),
                        flt(other_ded),
                        flt(payment_received),
                        (flt(r.project_value)+flt(price_adjustment)-flt(advance_adjusted)-flt(tds_amount)-flt(other_ded)-flt(payment_received)),
                        r.branch,
                        r.cost_center,
                        r.owner,
                        r.creation,
                        r.modified_by,
                        r.modified
                ))
            return tuple(data)
        else:
            return frappe.db.sql(query)
        

def get_conditions(filters):
        cond = []

        if filters.get("project"):
                cond.append('name = "{0}"'.format(filters.get("project")))

        if filters.get("branch"):
                cond.append('branch = "{0}"'.format(filters.get("branch")))

        if filters.get("cost_center"):
                cond.append('cost_center = "{0}"'.format(filters.get("cost_center")))

        if filters.get("from_date"):
                cond.append("expected_start_date >= \'{0}\'".format(str(filters.get("from_date"))))

        if filters.get("to_date"):
                cond.append("expected_end_date <= \'{0}\'".format(str(filters.get("to_date"))))
        
        if cond:
                query = str("where ")+str(" and ".join(cond))
        else:
                query = ""

        return query
