# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, add_days, cstr, getdate, nowdate, rounded, date_diff

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_data(filters):
    data = []
    cond = " and 1 =1"
    if filters.get("branch"):
        cond += " and e.branch = '{0}'".format(filters.branch)
            
        if filters.get("include_disabled"):
            cond += " and e.enabled = 1"

    equipments = """
        select * from (select e.name, e.branch, eo.start_date, ifnull(eo.end_date, curdate()) as to_date, 
        e.equipment_type from `tabEquipment` e, `tabEquipment Operator` eo  where eo.parent = e.name {0} group by e.name, e.branch) 
        as equip left join
        (select eo.operator, eo.start_date, ifnull(eo.end_date, curdate()) as end_date, eo.parent 
        from `tabEquipment Operator` eo)
        as opr 
        on opr.parent = equip.name 
    """.format(cond)
    filter_date  = " between '{0}' and '{1}'".format(filters.from_date, filters.to_date) 
    for eq in frappe.db.sql(equipments, as_dict=True):
        date = " between '{0}' and '{1}'".format(eq.from_date, eq.to_date)
        gross_pay = tc = le = ot = 0.0
        if eq.operator:
            date = " between '{0}' and '{1}'".format(eq.start_date, eq.end_date)
        if eq.employee_type == "Employee":
            # Get Travel Claim
            tc_result = frappe.db.sql("""
                select sum(ifnull(tc.total_claim_amount,0)) as travel_claim
                from `tabTravel Claim` tc 
                where tc.employee = '{0}'
                and   tc.docstatus = 1
                and tc.branch = '{2}' and tc.posting_date {1} and tc.posting_date {3}
            """.format(eq.operator, date, eq.branch, filter_date), as_dict=True)
            tc = flt(tc_result[0].travel_claim) if tc_result else 0.0

            # Get Leave Encashment Amount
            lea_result = frappe.db.sql("""
                select sum(ifnull(le.encashment_amount,0)) as e_amount 
                from `tabLeave Encashment` le
                where le.employee = '{0}'
                and   le.docstatus = 1 and le.branch = '{3}'
                and   le.encashment_date {1} and le.encashment_date {2}
            """.format(eq.operator, date, filter_date, eq.branch), as_dict=True)
            le = flt(lea_result[0].e_amount) if lea_result else 0.0

            # Get Overtime Amount
            ota_result = frappe.db.sql("""
                select sum(ifnull((ot.rate*oti.number_of_hours), 0)) as amount from `tabOvertime Application` ot, 
                `tabOvertime Application Item` oti 
                where oti.parent = ot.name and ot.docstatus = 1 and 
                oti.date {0} and ot.employee = '{1}'  and oti.date {2} and ot.branch = '{3}'
            """.format(date, eq.operator, filter_date, eq.branch), as_dict=True)
            ot = flt(ota_result[0].amount) if ota_result else 0.0

            # Process Salary
            sal = frappe.db.sql("""
                select ss.name, ss.employee, ss.branch,  ss.gross_pay, ssi.from_date, ssi.to_date
                from `tabSalary Slip` ss, `tabSalary Slip Item` ssi 
                where ss.employee = '{0}' and ssi.parent = ss.name
                and ss.docstatus = 1
                and ss.branch = '{1}' and (((ssi.from_date {2}) or (ssi.to_date {2})) or (( '{3}' {5}) or ('{4}' {5}))) and '{3}' 
                <= '{6}' 
            """.format(eq.operator, eq.branch, date, eq.start_date, eq.end_date, ss_date, filters.to_date), as_dict=True)

            if sal:
                gross_pay = 0.0
                for s in sal:
                    total_days = flt(date_diff(s.to_date, s.from_date) + 1)
                    s_start_date = getdate(s.from_date)
                    s_end_date = getdate(s.to_date)
                    f_from_date = getdate(filters.from_date)
                    f_to_date = getdate(filters.to_date)
                    if f_from_date <= s_start_date and s_end_date <= f_to_date:
                        if f_from_date < getdate(eq.start_date) < f_to_date:
                            work_date = flt(date_diff(s_end_date, eq.start_date) + 1)
                            gross_pay += flt(s.gross_pay) * flt(work_date) / flt(total_days)
                        elif f_from_date < getdate(eq.end_date) < f_to_date:
                            work_date = flt(date_diff(eq.end_date, f_from_date) + 1)
                            gross_pay += flt(s.gross_pay) * flt(work_date) / flt(total_days)
                        else:
                            gross_pay += flt(s.gross_pay)
                    if getdate(eq.end_date) < f_from_date:
                        gross_pay = 0.0
                    if s_start_date < f_from_date < s_end_date and s_start_date < f_to_date < s_end_date:
                        work_date = flt(date_diff(s_start_date, f_from_date) + 1)
                        gross_pay += flt(s.gross_pay) * flt(work_date) / flt(total_days)
                    if s_start_date < f_from_date and f_from_date <= s_end_date <= f_to_date and getdate(eq.end_date) > f_from_date:
                        work_date = flt(date_diff(s_end_date, f_from_date) + 1)
                        gross_pay += flt(s.gross_pay) * flt(work_date) / flt(total_days)
                    if f_from_date <= s_start_date <= f_to_date and s_end_date > f_to_date:
                        work_date = flt(date_diff(f_to_date, s_start_date) + 1)
                        gross_pay += flt(s.gross_pay) * flt(work_date) / flt(total_days)

        pol, insurance = equipment_expense(filters, eq.name, eq.branch, date, filter_date)
        total = flt(pol) + flt(insurance) + flt(gross_pay) + flt(le) + flt(tc) + flt(ot)
        row = [eq.name, eq.branch, eq.equipment_type, eq.operator, pol, insurance, gross_pay, le, tc, ot, total]
        data.append(row)
    return data

def equipment_expense(filters, eq_name, eq_branch, date, filter_date):    
    # Get POL
    pol_result = frappe.db.sql("""
        select (sum(qty*rate)/sum(qty)) as rate
        from `tabPOL Receive`
        where branch = '{0}'
        and   docstatus = 1 and posting_date {1} and posting_date {2}
    """.format(eq_branch, date, filter_date), as_dict=True)
    pol = flt(pol_result[0].rate) if pol_result else 0.0

    # Get Insurance
    ins_result = frappe.db.sql("""
        select sum(ifnull(id.total_amount,0)) as insurance  
        from `tabInsurance Details` id, `tabInsurance and Registration` ir 
        where id.parent = ir.name
        and   id.insured_date {0} and id.insured_date {1}
    """.format(date, filter_date), as_dict=True)
    insurance = flt(ins_result[0].insurance) if ins_result else 0.0

    return pol, insurance

def get_columns(filters):
    cols = [
        ("ID") + ":Link/Equipment:120",
        ("Branch") + ":Data:120",
        ("Equipment Type") + ":Data:120",
        ("Operator/Driver") + ":Data:120",
        ("HSD Consumption") + ":Float:120",
        ("Tax & Insurance") + ":Float:120",
        ("Gross Pay") + ":Float:120",
        ("Leave Encashment") + ":Currency:120",
        ("Travel Claim") + ":Float:120",
        ("OT Amount") + ":Float:120",
        ("Total Expense") + ":Float:120"
    ]
    return cols