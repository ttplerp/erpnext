import frappe
from erpnext.setup.doctype.employee.employee import create_user
import csv
from frappe.utils import flt, cint, nowdate, getdate, formatdate
import math
from frappe import _

from erpnext.integrations.bps import process_files
from erpnext.assets.doctype.asset.depreciation import make_depreciation_entry
from hrms.hr.doctype.leave_application.leave_application import (
    get_leave_balance_on,
    get_leaves_for_period,
    get_leave_entries,
    get_holidays
)
from typing import Dict, Optional, Tuple
from hrms.hr.utils import (
    get_holiday_dates_for_employee,
    get_leave_period,
    set_employee_name,
    share_doc_with_approver,
    validate_active_employee,
)
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
import calendar
from datetime import datetime
from frappe.utils import (
    add_days,
    cint,
    cstr,
    date_diff,
    flt,
    formatdate,
    get_fullname,
    get_link_to_form,
    getdate,
    nowdate,
)

def treasury_term():
    count = 1
    for a in frappe.db.get_all("Treasury", {"type_of_instrument": "Bond"}, ['name', 'day']):
        term = flt(a.day/365,0)
        print(str(count)+". "+str(term))
        count += 1
        # frappe.db.

def update_advance_ss():
    for a in frappe.db.sql("""select a.name, a.monthly_deduction, a.employee, a.advance_amount
                                from `tabEmployee Advance` a
                                where a.docstatus=1 and a.workflow_state="Claimed"
                                and not exists(
                                    select 1 from `tabEmployee Advance Settlement` s
                                    where s.employee_advance_id = a.name
                                )
                    """, as_dict=True):
        total_deducted = 0.00
        os_amount = flt(a.advance_amount,2)
        ss = None
        for b in frappe.db.sql("""
                            SELECT name, parenttype, amount, total_deductible_amount, total_deducted_amount,  
                                total_outstanding_amount, creation  
                            FROM `tabSalary Detail` 
                            WHERE salary_component ='Salary Advance Deductions'  
                            AND reference_number = '{}'
                            order by creation asc
                    """.format(a.name), as_dict=True):
            if a.monthly_deduction == b.amount and b.parenttype=="Salary Slip":
                total_deducted += b.amount
                os_amount -= b.amount
                frappe.db.sql("""update `tabSalary Detail` 
                        set total_outstanding_amount='{0}',total_deducted_amount='{1}'
                        where name='{2}' """.format(os_amount, total_deducted, b.name))
            if b.parenttype=="Salary Structure":
                ss=b.name

        frappe.db.sql("""update `tabSalary Detail` 
                        set total_outstanding_amount='{0}',total_deducted_amount='{1}'
                        where name='{2}' """.format(os_amount, total_deducted, ss))
        frappe.db.commit()
        print("Employee Final:", a.employee, total_deducted, os_amount)
        
def make_pev_draft():
    count = 1
    for pev in frappe.db.sql("""
                             select name from `tabPerformance Evaluation` where workflow_state = 'Approved'
                             """,as_dict=1):
        frappe.db.sql("""
                      update `tabPerformance Evaluation` set docstatus = 0, workflow_state = 'Draft' where name = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabEvaluate Target Item` set docstatus = 0 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabEvaluate Additional Achievements` set docstatus = 0 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabEvaluate Competency` set docstatus = 0 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabLeadership Competency` set docstatus = 0 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabSupervisor Declaration` set docstatus = 0 where parent = '{}'
                      """.format(pev.name))
        print(str(count)+". "+pev.name)
        count += 1
    for ped in frappe.db.sql("""
                             select name from `tabPerformance Evaluation` where workflow_state = 'Draft' and
                             name not in ("PEVA2502240015-1", "PEVA2502130004", "PEVA2502250041", "PEVA2502260004")
                             """,as_dict=1):
        doc = frappe.get_doc("Performance Evaluation", ped.name)
        doc.save(ignore_permissions=True)

def make_pev_approved():
    count = 1
    for pev in frappe.db.sql("""
                             select name from `tabPerformance Evaluation` where workflow_state = 'Draft'
                             and name not in ("PEVA2502240015-1", "PEVA2502130004", "PEVA2502250041", "PEVA2502260004")
                             """,as_dict=1):
        frappe.db.sql("""
                      update `tabPerformance Evaluation` set docstatus = 1, workflow_state = 'Approved' where name = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabEvaluate Target Item` set docstatus = 1 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabEvaluate Additional Achievements` set docstatus = 1 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabEvaluate Competency` set docstatus = 1 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabLeadership Competency` set docstatus = 1 where parent = '{}'
                      """.format(pev.name))
        frappe.db.sql("""
                      update `tabSupervisor Declaration` set docstatus = 1 where parent = '{}'
                      """.format(pev.name))
        print(str(count)+". "+pev.name)
        count += 1

def check_asset_gross_rate():
    i=1
    for a in frappe.db.sql("""
                            select name, gross_purchase_amount, asset_rate
                            from `tabAsset` where gross_purchase_amount!=asset_rate
                            order by name
                        """, as_dict=True):
        print(a.name, a.gross_purchase_amount, a.asset_rate , i)
        #frappe.db.sql("update `tabAsset` set asset_rate='{}' where name='{}'".format(a.gross_purchase_amount, a.name))
        i+=1
    #frappe.db.commit()

def delete_transaction_treasury():
    for a in frappe.db.sql("""
                           select name from `tabJournal Entry` where title like '%Treasury%'
                           """,as_dict=1):
        frappe.db.sql("delete from `tabJournal Entry` where name = '{}'".format(a.name))
        frappe.db.sql("delete from `tabJournal Entry Account` where parent = '{}'".format(a.name))
        frappe.db.sql("delete from `tabGL Entry` where voucher_no = '{}'".format(a.name))
        for b in frappe.db.sql("""
                               select name, cbs_entry from `tabCBS Entry Upload` where voucher_no = '{}'
                               """.format(a.name),as_dict=1):
            frappe.db.sql("delete from `tabCBS Entry Upload` where name = '{}'".format(b.name))
            frappe.db.sql("delete from `tabCBS Entry Log` where parent = '{}'".format(b.cbs_entry))
            frappe.db.sql("delete from `tabCBS Entry` where name = '{}'".format(b.cbs_entry))
        print(a.name)


def uncancel_asset():
    for a in frappe.db.sql("""
                           select name from `tabAsset` where docstatus = 2 and name like '%BDBL/E%' and
                           asset_category = 'Furniture & Fixtures'
                           """,as_dict=1):
        frappe.db.sql("""
                      update `tabAsset` set docstatus = 0 where name = '{}'
                      """.format(a.name))
        print(a.name)

# def check_missing_de_link():
#     df = pd.read_excel(r"/home/frappe/erp/apps/erpnext/erpnext/Dep ISSUE_2023.xlsx")
#     df = df.to_dict()
#     row1 = row2 = 0
#     count  = 0
#     for a in df.get('asset'):
#         # if df.get('difference')[a]
#         if flt(df.get('Difference')[a]) > 1:
#             jes = frappe.db.sql("""
#                     select je.name from `tabJournal Entry` je, `tabJournal Entry Account` jea where je.remark like '%Depreciation Entry against%' and jea.parent = je.name
#                     and year(je.posting_date) = 2023 and jea.reference_name = '{0}' and je.docstatus = 1 group by je.name
#             """.format(df.get('asset')[a]), as_dict=1)
#             if jes:
#                 for b in jes:
#                     if not frappe.db.exists("Depreciation Schedule", {"journal_entry": b.name, "parent": df.get('asset')[a]}):
#                         print(str(count)+". "+str(b.name))
#                         je_doc = frappe.get_doc("Journal Entry", b.name)
#                         je_doc.cancel()
#                         if (count+1)%100 == 0:
#                             frappe.db.commit()
#                         count += 1
#         # row1 += 1
#     # print(df.get('asset')[0]+" "+str(df.get('Difference')[0]))
#     # for a in df.asset:
#     #     print(str(a))
#     # count = 1
#     # assets = frappe.db.sql("""

#     #                     """,as_dict = 1)
#     # if assets:
#     #     for a in assets:
#     #         asset_doc = frappe.get_doc("Asset", a.against_voucher)
#     #         # for b in asset_doc.schedules:
#     #         print(str(count)+". "+a.against_voucher)
#     #         count+=1
def update_interest_jv():
    for ia in frappe.db.sql("""
                            select ia.name, ia.posting_date from `tabInterest Accrual` ia where ia.journal_entry is not null and not exists(select 1 from `tabJournal Entry` je where je.name = ia.journal_entry) and ia.docstatus = 1
                            """,as_dict=1):
        frappe.db.sql("""update `tabInterest Accrual` set fiscal_year = '{}' where name = '{}'""".format(str(ia.posting_date).split("-")[0], ia.name))
        print(ia.name)
def asset_account_update():
    i=1
    acc="120060005 - Clearing Account Migration - BDBL"
    for a in frappe.db.sql(""" select name, credit_account from `tabAsset` 
                              where docstatus=0
                              and name not in ("BDBL/F-CRP-00049","BDBL/E-TVS-00068","BDBL/C-MON-00270")
                              and credit_account="120060004 - Stock Asset - BDBL"
                        """, as_dict=True):
        i+=1
        print(i, a.name, a.credit_account)
        frappe.db.sql("update `tabAsset` set credit_account='{}' where name='{}'".format(acc, a.name))
    frappe.db.commit()
        
def update_stock_account():
    acc="120060005 - Clearing Account Migration - BDBL"
    for a in frappe.db.sql(""" select name from `tabAsset` 
                              where docstatus=1 
                              and name not in ("BDBL/F-CRP-00049","BDBL/E-TVS-00068","BDBL/C-MON-00270")
                              and credit_account="120060004 - Stock Asset - BDBL"
                        """, as_dict=True):
        for b in frappe.db.sql(""" select name, parent, account from `tabJournal Entry Account`
                                    where reference_name='{0}' and account="120060004 - Stock Asset - BDBL"
                                """.format(a.name), as_dict=True):
            for c in frappe.db.sql("""select name, voucher_no from `tabGL Entry`
                                    where account='{0}' and voucher_no='{1}'
                                """.format(b.account, b.parent), as_dict=True):
                print(a.name, b.name, b.parent, b.account, c.name)
                frappe.db.sql("update `tabGL Entry` set account='{}' where name='{}'".format(acc, c.name))
                frappe.db.sql("update `tabJournal Entry Account` set account='{}' where name='{}'".format(acc, b.name))
                frappe.db.sql("update `tabJournal Entry` set title='{}' where name='{}' and title='{}'".format(acc,b.parent,b.account))
                frappe.db.sql("update `tabAsset` set credit_account='{}' where name='{}'".format(acc, a.name))
            frappe.db.commit()

def submit_asset_feb():
    i=1
    for a in frappe.db.sql(""" select name from `tabAsset` 
                              where docstatus=0
                              limit 1000
                        """, as_dict=True):
        doc = frappe.get_doc("Asset", a.name)
        i+=1
        print(i, doc.name, " Submitting ongoing")
        doc.submit()

def delete_asset_feb():
    for d in frappe.db.sql("select name from `tabAsset` where name not in ('BDBL/F-CRP-00049','BDBL/E-TVS-00068','BDBL/C-MON-00270')", as_dict=1):
        print(d.name)
        frappe.db.sql("delete from `tabAsset Finance Book` where parent='{}'".format(d.name))
        frappe.db.sql("delete from `tabDepreciation Schedule` where parent='{}'".format(d.name))
        frappe.db.sql("delete from `tabAsset` where name='{}'".format(d.name))
    frappe.db.commit()

def delete_je_last_year():
    count = 1
    for je in frappe.db.sql("""select name, posting_date from `tabJournal Entry` where posting_date < '2025-01-01' """,as_dict=1):
        print(je.name, je.posting_date)
        frappe.db.sql("""
                        delete from `tabGL Entry` where voucher_no = '{}'
                        """.format(je.name))
        frappe.db.sql("""
                        delete from `tabPayment Ledger Entry` where voucher_no = '{}'
                        """.format(je.name))
        frappe.db.sql("""
                        delete from `tabJournal Entry` where name = '{}'
                        """.format(je.name))
        frappe.db.sql("""
                        delete from `tabJournal Entry Account` where parent = '{}'
                        """.format(je.name))
        count+=1
        print(str(count)+". "+je.name)
    frappe.db.commit()

def update_asset_opening_account():
    count = 1
    for asset in frappe.db.get_all("Asset", {"docstatus": 1}):
        for jva in frappe.db.get_all("Journal Entry Account", {"reference_name": asset.name, "account": "120060004 - Stock Asset - BDBL"}, ["name"]):
            frappe.db.sql("update `tabJournal Entry Account` set account = '{}' where name = '{}'".format("120060005 - Clearing Account Migration - BDBL", jva.name))
        for gle in frappe.db.get_all("GL Entry", {"against_voucher": asset.name, "account": "120060004 - Stock Asset - BDBL"}, ["name"]):
            frappe.db.sql("update `tabGL Entry` set account = '{}' where name = '{}'".format("120060005 - Clearing Account Migration - BDBL", gle.name))
        print(str(count)+". "+asset.name)
        count += 1

def delete_gl_today():
    frappe.db.sql("delete from `tabGL Entry` where posting_date between '2024-01-01' and '2024-12-31'")
    frappe.db.sql("delete from `tabPayment Ledger Entry` where posting_date between '2024-01-01' and '2024-12-31'")
    frappe.db.commit()

def update_travel():
    #make TC draft
    tc="TC250200049"
    ta="TA250100017"

    '''
    frappe.db.sql("delete from `tabTravel Authorization` where name='{}'".format(ta))
    frappe.db.sql("delete from `tabTravel Authorization Item` where parent='{}'".format(ta))

    frappe.db.sql("delete from `tabTravel Claim` where name='{}'".format(tc))
    frappe.db.sql("delete from `tabTravel Claim Item` where parent='{}'".format(tc))
    '''

    frappe.db.sql("update `tabTravel Authorization` set docstatus='0', workflow_state='Draft' where name='{}'".format(ta))
    frappe.db.sql("update `tabTravel Authorization Item` set docstatus='0' where parent='{}'".format(ta))
    
    '''
    frappe.db.sql("update `tabTravel Claim` set docstatus='0', workflow_state='Draft' where name='{}'".format(tc))
    frappe.db.sql("update `tabTravel Claim Item` set docstatus='0' where parent='{}'".format(tc))
    '''
    frappe.db.commit()


def update_swl():
    i=0
    for a in frappe.db.sql("""select parenttype, name, reference_type, salary_component 
                    from `tabSalary Detail` where salary_component="SWL"
                    """, as_dict=True):
        i+=1
        print(i, a.name, a.reference_type, a.salary_component, a.parenttype)
        frappe.db.sql("update `tabSalary Detail` set reference_type='Staff Welfare Loan' where name='{}'".format(a.name))
    frappe.db.commit()

def check_gl_pl():
    for a in frappe.db.sql("""
                        select voucher_no, voucher_type from `tabGL Entry`
                    """, as_dict=True):
        if not frappe.db.exists(a.voucher_type, a.voucher_no):
            print(a.voucher_type, a.voucher_no)
            frappe.db.sql("delete from `tabGL Entry` where voucher_no='{}'".format(a.voucher_no))
            frappe.db.sql("delete from `tabPayment Ledger Entry` where voucher_no='{}'".format(a.voucher_no))
    frappe.db.commit()

def post_le():
    i=1
    for a in frappe.db.sql("""
                        select name, journal_entry from `tabLeave Encashment`
                        where docstatus=1 and employee not in ("0827","0294","0275","0626","0640")
                        and encashment_date > "2024-12-31"
                        and journal_entry is NULL
                        and name not in ("HR-ENC-2025-00086","HR-ENC-2025-00087")
                    """, as_dict=True):
        print(i, a.name, a.journal_entry)
        doc = frappe.get_doc("Leave Encashment", a.name)
        doc.post_accounts_entry()
        i+=1
    frappe.db.commit()

def update_le_ea():
    for a in frappe.db.sql("""select  jd.reference_name as ref_name, jd.reference_type
                        from `tabJournal Entry` je inner join `tabJournal Entry Account` jd on je.name=jd.parent
                        where jd.reference_type in ("Leave Encashment","Employee Advance")
                        and je.docstatus=1
                        group by jd.reference_name
                        """, as_dict=True):
        doc = frappe.get_doc(a.reference_type, a.ref_name)
        if doc.workflow_state=="Approved":
            frappe.db.sql("Update `tab{}` set workflow_state='Claimed' where name='{}'".format(a.reference_type, a.ref_name))


        print(a.ref_name, a.reference_type, doc.workflow_state)
    frappe.db.commit()

def delete_journal_entry():
    for a in frappe.db.sql("select name from `tabJournal Entry` where name in ('JEJV20250100197')", as_dict=True):
        frappe.db.sql("delete from `tabGL Entry` where voucher_no='{}'".format(a.name))
        frappe.db.sql("delete from `tabJournal Entry Account` where parent='{}'".format(a.name))
        frappe.db.sql("delete from `tabPayment Ledger Entry` where voucher_no='{}'".format(a.name))
        frappe.db.sql("delete from `tabJournal Entry` where name='{}'".format(a.name))
        frappe.db.commit()

def leave_encash():
    for a in frappe.db.sql("""
                    select je.name, jd.reference_type, jd.reference_name from `tabJournal Entry` je inner join `tabJournal Entry Account` jd on je.name=jd.parent
                    where jd.reference_name in (
                            select name from `tabLeave Encashment`
                                where docstatus=1 and employee not in ("0827","0294","0275","0626","0640")
                                and posting_date > "2024-12-31"
                        )
                    and jd.reference_type="Leave Encashment"
                    and jd.docstatus !=2
                            """, as_dict=True):
        #frappe.db.sql("delete from `tabJournal Entry` where name='JEBE20250100390'".format(a.name))
        #frappe.db.sql("delete from `tabJournal Entry Account` where parent='JEBE20250100390' ".format(a.name))
        #frappe.db.sql("update `tabLeave Encashment` set journal_entry=NULL where name='{}'".format(a.reference_name))
        print(a.reference_name, a.name)        
    #frappe.db.commit()         
       
    #doc = frappe.get_doc("Leave Encashment","HR-ENC-2025-00209")
    #doc.post_accounts_entry()

def delete_sa_component():
    for a in frappe.db.sql("""select st.name, st.employee_name, sd.name as child_name from `tabSalary Detail` sd 
                join `tabSalary Structure` st on sd.parent=st.name 
                where st.docstatus!=2
                and parentfield="deductions"
                and ((sd.to_date is NULL or sd.to_date="") or sd.to_date < '2024-12-31')
            """, as_dict=True):
        '''
        doc = frappe.get_doc("Salary Structure", a.name)
        rem_list = []
        for b in doc.get("deductions"):
            if b.name == a.child_name:
                rem_list.append(b)

        [doc.remove(a) for a in rem_list]
        doc.save(ignore_permissions=True)
        '''
        print(a.name, a.employee_name)

def delete_leave_encash():
    for a in frappe.db.sql("select name from `tabLeave Encashment` where name='' and docstatus !=1", as_dict=True):
        frappe.db.sql("delete from `tabLeave Encashment` where name='{}'".format(a.name))
    frappe.db.commit()

def change_je_date():
    for a in frappe.db.sql("""select name, posting_date from `tabJournal Entry` 
                        where reference_type='Payroll Entry' 
                        and posting_date > '2024-12-31' 
                    """,as_dict=True):
        #print(a.name, a.posting_date, b.name,b.posting_date)
        frappe.db.sql("""update `tabGL Entry` 
                    set posting_date='2024-12-31' 
                    where voucher_no='{}' and voucher_type='Journal Entry'
                """.format(a.name))
        frappe.db.sql("update `tabJournal Entry` set posting_date='2024-12-31' where name='{}'".format(a.name))
    frappe.db.commit()

def reset_password():
    for a in frappe.db.sql("select name from `tabUser` where enabled=1 and name!='Administrator'", as_dict=True):
        if frappe.db.exists("Employee", {"user_id": a.name}):
            emp = frappe.get_doc("Employee", {"user_id": a.name})
            doc = frappe.get_doc("User", a.name)
            from datetime import datetime
            date_object = datetime.strptime(str(emp.date_of_birth), "%Y-%m-%d")
            date_dd_mm = str(date_object.strftime("%d"))+str(date_object.strftime("%m"))
            new_password = "bdb@" + date_dd_mm
            doc.new_password = new_password
            doc.save()
            recipients = str(a.name)
            subject = "Password Changed Notice"
            message = "Your ERP Password is changed to : {}".format(new_password)
            frappe.sendmail(
                recipients=recipients,
                subject=_(subject),
                message= _(message),
            )    
            print(emp.employee, date_dd_mm, new_password)
        else:
            print(a.name, "No Employee")

def submit_asset_today():
    i = 0
    for a in frappe.db.sql("""
                            select name from `tabAsset`
                            where docstatus=0
                    """, as_dict=True):
        doc = frappe.get_doc("Asset", a.name)
        value_after_depreciation = flt(doc.gross_purchase_amount) - flt(
				doc.income_tax_opening_depreciation_amount
			)
        print(value_after_depreciation)
        frappe.db.sql("""update `tabAsset Finance Book` set value_after_depreciation='{}'
                        where parent='{}'
                        """.format(value_after_depreciation, a.name))
        frappe.db.commit()
        doc.submit()
        i+=1
        print(i)

def submit_ss():
    i=1
    for a in frappe.db.sql("select name from `tabSalary Slip` where payroll_entry='HR-PRUN-2025-00001' and docstatus=0", as_dict=True):
        doc = frappe.get_doc("Salary Slip", a.name)
        i+=1
        print(i, a.name)
        doc.submit()

def delete_ss():
    for a in frappe.db.sql("select *from `tabPayroll Entry` where name in ('HR-PRUN-2025-00003')", as_dict=True):
        if a.docstatus !=2:
            for b in frappe.db.sql("select name from `tabSalary Slip` where payroll_entry='{}'".format(a.name), as_dict=True):
                frappe.db.sql("Delete from `tabSalary Detail` where parent='{}'".format(b.name))
                frappe.db.sql("Delete from `tabOvertime Item` where parent='{}'".format(b.name))
                frappe.db.sql("Delete from `tabSalary Slip Timesheet` where parent='{}'".format(b.name))
                frappe.db.sql("Delete from `tabSalary Slip Item` where parent='{}'".format(b.name))
                frappe.db.sql("Delete from `tabSalary Slip` where name='{}'".format(b.name))
    frappe.db.commit()

    
'''
section_list=[
        # {
        #     "division":"HR & Logistics Division - BDBL",
        #     "branch" : "Human Resource & Administration",
        #     "cost_center" : "0000 - Human Resource & Administration - BDBL"
        # },
        # {
        #     "division":"Risk Management Division - BDBL",
        #     "branch" : "Risk Management",
        #     "cost_center" : "0000 - Risk Management - BDBL"
        # },
        # {
        #     "division":"Legal Division - BDBL",
        #     "branch" : "Legal",
        #     "cost_center" : "0000 - Legal - BDBL"
        # },
        # {
        #     "division":"CEO's Office - BDBL",
        #     "branch" : "Office of CEO",
        #     "cost_center" : "0000 - Office of CEO - BDBL"
        # },
        # {
        #     "division":"Internal Audit  - BDBL",
        #     "branch" : "Internal Audit",
        #     "cost_center" : "0000 - Internal Audit - BDBL"
        # },
        # {
        #     "division":"Finance & Accounts Division - BDBL",
        #     "branch" : "Finance & Accounts",
        #     "cost_center" : "0000 - Finance & Accounts - BDBL"
        # },
        # {
        #     "division":"ICT & Digital Banking Division - BDBL",
        #     "branch" : "ICT & Digital Banking",
        #     "cost_center" : "0000 - ICT & Digital Banking - BDBL"
        # },
        # {
        #     "division":"Policy & Planning Division- BDBL",
        #     "branch" : "Credit",
        #     "cost_center" : "0000 - Credit - BDBL"
        # }
        
    ]
'''
from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_fullname,
	get_link_to_form,
	getdate,
	nowdate,
    add_to_date
)
import datetime

def update_icl():
    subject_list=frappe.db.sql("""select verifier_mail, verifier_type 
                            from `tabInternal Audit Clearance Verifier List` 
                            where parent ='Audit Settings' 
                            and ( parentfield='verifier' or parentfield='approver' )
                        """, as_dict=True)
    icthr = []
    ictcr = []
    afd = []
    iad = []
    for subject in subject_list:
        if subject.verifier_type=="HR":
            icthr.append(subject.verifier_mail)
        if subject.verifier_type=="Credit":
            ictcr.append(subject.verifier_mail)
        if subject.verifier_type=="Finance":
            afd.append(subject.verifier_mail)
        if subject.verifier_type=="Audit":
            iad.append(subject.verifier_mail)

    for a in frappe.db.sql("""
                        select * from `tabInternal Clearance`
                      where docstatus !=2
                    """, as_dict=True):
            frappe.db.sql("""update `tabInternal Clearance` set 
                            afd="{0}", ictcr="{1}", icthr="{2}", iad="{3}" 
                            where name="{4}"
                    """.format(str(afd), str(ictcr), str(icthr), str(iad), a.name))
    frappe.db.commit()

def delete_employee_adv():
    for a in frappe.db.sql("select name, je_reference from `tabEmployee Advance` where advance_type='Salary Advance'", as_dict=True):
        frappe.db.sql("delete from `tabGL Entry` where voucher_no='{}'".format(a.je_reference))
        frappe.db.sql("delete from `tabJournal Entry Account` where parent='{}'".format(a.je_reference))
        frappe.db.sql("delete from `tabJournal Entry` where name='{}'".format(a.je_reference))
        frappe.db.sql("delete from `tabEmployee Advance` where name='{}'".format(a.name))
    frappe.db.commit()

def cancel_asset():
    count = 1
    for je in frappe.db.sql("""select distinct parent from `tabJournal Entry Account` where reference_type = 'Asset'""",as_dict=1):
        je_doc = frappe.get_doc("Journal Entry", je.parent)
        # je_doc.cancel()
        frappe.db.sql("""
                        delete from `tabGL Entry` where voucher_no = '{}'
                        """.format(je.parent))
        frappe.db.sql("""
                        delete from `tabJournal Entry` where name = '{}'
                        """.format(je.parent))
        frappe.db.sql("""
                        delete from `tabJournal Entry Account` where parent = '{}'
                        """.format(je.parent))
        print(str(count)+". "+je.parent)
        count += 1

def update_ic():
    for a in frappe.db.sql("""
                        select name, workflow_state,iad from `tabInternal Clearance`
                        where docstatus = 0 and workflow_state="Waiting for Verification"
                        and iad_clearance = 0
                """, as_dict=True):
        print(a.name, a.workflow_state, a.iad)
        frappe.db.sql("update `tabInternal Clearance` set iad='penjor@bdb.bt' where name='{}'".format(a.name))
    frappe.db.commit()

def submit_asset():
    count = 1
    for a in frappe.db.get_all("Asset", {"docstatus":0}):
        print(str(count)+". "+a.name)
        asset = frappe.get_doc("Asset", a.name)
        asset.save()
        asset.submit()
        count += 1

def save_asset():
    for a in frappe.db.sql("""
                           select name from `tabAsset` where docstatus = 0
                           """,as_dict=1):
        doc = frappe.get_doc("Asset", a.name)
        doc.save(ignore_permissions=1)
        print(a.name)

def update_ec():
    for a in frappe.db.sql("""
                        select name, docstatus, workflow_state from `tabExpense Claim`
                        where docstatus=1 and workflow_state="Approved"
                """, as_dict=True):
        frappe.db.sql("update `tabExpense Claim` set workflow_state = 'Claimed' where name='{}'".format(a.name))
        print(a.name, a.workflow_state, a.docstatus)
    frappe.db.commit()

def update_target():
    for dos in frappe.db.sql("select name from `tabTarget Set Up` where workflow_state!='Draft'", as_dict=True):
        doc = frappe.get_doc("Target Set Up", dos.name)
        frappe.db.sql("update `tabTarget Set Up` set workflow_state='Draft' where name = '{}'".format(doc.name), as_dict=True)
        # doc.save()
        # for childoc in frappe.db.sql("select name, docstatus from `tabPerformance Target Evaluation` where parent='{}'".format(dos.name), as_dict=True):
            # childoc.docstatus=0
            # doc.save(
            #     ignore_permissions=True, # ignore write permissions during insert
            #     ignore_version=True # do not create a version record
            # )
            # status=frappe.db.sql("update `tabPerformance Target Evaluation` set docstatus=0 where name = '{}'".format(childoc.name), as_dict=True)
            # print(status)
            # print(childoc.docstatus)
            # childoc.save()
        # doc.save()

def update_party_check_for_salary():
    for jea in frappe.db.get_all("GL Entry", {"voucher_no": ["in", ('JEBP20241100042', 'JEJV20241100044')]}):
        frappe.db.sql("""
                      update `tabGL Entry` set party_check = 0 where name = '{}'
                      """.format(jea.name))
        print(jea.name)
#
def delete_loan():
    for a in frappe.db.sql("""
                    select name, parent, salary_component from `tabSalary Detail` where salary_component in ('Salary Saving Scheme')
                """, as_dict=1):

        # if a.parent=="0171/SST/00001":
            # print(a.salary_component)
        doc = frappe.get_doc("Salary Detail", a.name)
        print(f"{doc.parent}               {doc.salary_component}       {doc.name}")
        frappe.delete_doc("Salary Detail", a.name)
        
def update_branch_code():
    for a in frappe.db.get_all("Branch", filters={"branch_code": ["in", (None, "")]}, fields=['name', 'cost_center']):
        cc_code = frappe.db.get_value("Cost Center", a.cost_center, "cost_center_number")
        frappe.db.sql("""
                      update `tabBranch` set branch_code = '{}' where name = '{}'
                      """.format(cc_code, a.name))
        print(a.name)

def check_ifrs_dep():
    with open("/home/frappe/erp/update_dep_check.csv") as f:
        reader = csv.reader(f)
        mylist = list(reader)
        c = 0
        for i in mylist:
            if c > 0:
                doc=frappe.get_doc("Asset", str(i[0]))
                diff = flt(doc.opening_accumulated_depreciation,2) - flt(i[1],2)
                if diff != 0:
                    print(doc.name, doc.opening_accumulated_depreciation, str(i[1]), diff)
            #print(i[0]) #print(str(i[0], str(i[1])))
            c += 1

def asset_update_ifrs():
    with open("/home/frappe/erp/update_depv1.csv") as f:
        reader = csv.reader(f)
        mylist = list(reader)
        c = 0
        for i in mylist:
            if c >11992 and c < 22000:
                asset_id = str(i[1])
                #print(str(i[1]), str(i[0]))
                if frappe.db.exists("Asset", str(i[0])):
                    doc = frappe.get_doc("Asset", str(i[0]))
                    doc.opening_accumulated_depreciation = flt(str(i[1]),2)
                    doc.save()
                    print(c, doc.name, str(i[1]), doc.opening_accumulated_depreciation)
                else:
                    print(c, "Cannot Find")
            c += 1
            

def add_loan_component():
    with open("/home/frappe/erp/ERP_upload_details.csv") as f:
        reader = csv.reader(f)
        mylist = list(reader)
        c = 1
        for i in mylist:
            desuup_cid = str(i[1])
            doc = frappe.get_doc("Salary Strcuture", {"employee":str[1]})
            if doc:
                if not frappe.db.exists("Salary Details", {"parentfield":"deductions", "parent":doc.name, "componenet_type":'FI Own Loan'}):
                    doc.append("deductions",{
                        'salary_component': "FI Own Loan",
                        'amount': 23423,
                        'fina':''
                    })
                doc.save()
    
def test():
    frm_date="2024-09-01"
    to_date="2024-10-26"
    no_days=date_diff(to_date, frm_date)+1
    
    print(no_days)
    final=no_days
    total_days=0
    is_sat=frappe.db.get_value("Holiday List", "Thimphu Holiday 2024", "saturday_half")
    cur_date=frm_date
    
    con=frappe.db.sql("select * from `tabHoliday` where parent='Thimphu Holiday 2024'", as_dict=1)
    
    for i in range(0, no_days):
        
        for holiday in frappe.db.sql("select * from `tabHoliday` where parent='Thimphu Holiday 2024'", as_dict=1):
            
            # if holiday.holiday_date.weekday==5:
            #     total_days+=0.5   
            
            # print(holiday.holiday_date==datetime.date(int(cur_date[:4]), int(cur_date[5:7]), int(cur_date[8:])))
            if holiday.holiday_date==datetime.date(int(cur_date[:4]), int(cur_date[5:7]), int(cur_date[8:])):
                # print(datetime.date(int(cur_date[:4]), int(cur_date[5:7]), int(cur_date[8:])))
                if holiday.holiday_date.weekday()==5:
                    
                    print(f"Saturday: date {cur_date} holiday {holiday.holiday_date}" )
                    final-=0.5   
                else:
                    final-=1
                    print(f"Sunday date {cur_date} holiday {holiday.holiday_date}" )
                    
                
                
        cur_date=add_to_date(getdate(cur_date), days=1, as_string=True)
        
    print("Total Holliday: ", final)
            
            
            
    
def save_salary_struc():
    for a in frappe.db.sql("""
                           select name from `tabSalary Structure` where is_active='yes'
                           """, as_dict=1):
        print(a)
    
        doc = frappe.get_doc("Salary Structure",a.name)
        doc.save()

def checkfunc():
    leave_entries=get_leave_entries('0521', 'Casual Leave', '2024-01-01', '2024-12-31')
    leave_days = 0
    for leave_entry in leave_entries:
        if leave_entry.transaction_type == "Leave Application":
            half_day = 0
            half_day_date = None
            # fetch half day date for leaves with half days
            if leave_entry.leaves % 1:
                half_day = 1
                half_day_date = frappe.db.get_value(
                    "Leave Application", {"name": leave_entry.transaction_name}, ["half_day_date"]
                )
                
            leave_days += (
                get_number_of_leave_days(
                    '0521',
                    'Casual Leave',
                    leave_entry.from_date,
                    leave_entry.to_date,
                    half_day,
                    half_day_date,
                    holiday_list=leave_entry.holiday_list,
                )
                * -1)

    print(leave_days)

def get_number_of_leave_days(
    employee: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    half_day: Optional[int] = None,
    half_day_date: Optional[str] = None,
    holiday_list: Optional[str] = None,
) -> float:
    """Returns number of leave days between 2 dates after considering half day and holidays
    (Based on the include_holiday setting in Leave Type)"""
    number_of_days = 0
    if not holiday_list:
        holiday_list = get_holiday_list_for_employee(employee)
    if cint(half_day) == 1:
        
        if getdate(from_date) == getdate(to_date):
            number_of_days = 0.5
        elif half_day_date and getdate(from_date) <= getdate(half_day_date) <= getdate(to_date):
            number_of_days = date_diff(to_date, from_date) + 0.5
        else:
            number_of_days = date_diff(to_date, from_date) + 1
    else:
        number_of_days = date_diff(to_date, from_date) + 1
    
    if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
        
        number_of_days = flt(number_of_days) - flt(
            get_holidays(employee, from_date, to_date, holiday_list=holiday_list)
        )
        
        half = frappe.db.get_value("Holiday List", get_holiday_list_for_employee(employee), "saturday_half")
        d = from_date
        while(getdate(d) <= getdate(to_date)):
            day = calendar.day_name[datetime.strptime(str(getdate(d)).split(" ")[0],"%Y-%m-%d").weekday()]
            #For Saturday half day work time
            # if getdate(d).weekday() == 5 and flt(get_holidays(employee, d, d)) == 0 and half:
            # 	number_of_days-=0.5
            half_working_day = frappe.db.sql("""select day from `tabHoliday List Days` where parent = '{}'""".format(holiday_list))
            for hwd in half_working_day:
                if day in hwd:
                    if not frappe.db.exists("Holiday",{"parent":holiday_list,"holiday_date":datetime.strptime(str(d).split(" ")[0],"%Y-%m-%d")}):
                        print(frappe.db.exists("Holiday",{"parent":holiday_list,"holiday_date":datetime.strptime(str(d).split(" ")[0],"%Y-%m-%d")}))
                        number_of_days -= 0.5
            d = frappe.utils.data.add_days(d, 1)
           
    return number_of_days   
    
def update_emp_dtl():
    section_list= [
    # {'section': '0010 - Thimphu Main Branch - BDBL', 'unit': None, 'branch': 'Thimphu Main Branch', 'cost_center': '0010 - Thimphu Main - BDBL'},
    # {'section': '0020 - Thimphu - BDBL', 'unit': None, 'branch': 'Thimphu', 'cost_center': '0020 - Thimphu - BDBL'},  
    # {'section': '0030 - Paro - BDBL', 'unit': None, 'branch': 'PARO', 'cost_center': '0030 - Paro - BDBL'}, 
    # {'section': '0040 - Wangdue - BDBL', 'unit': None, 'branch': 'WANGDUE', 'cost_center': '0040 - WANGDUE - BDBL'}, 
    # {'section': '0050 - Punakha - BDBL', 'unit': None, 'branch': 'PUNAKHA', 'cost_center': '0050 - PUNAKHA - BDBL'}, 
    # {'section': '0060 - Gasa - BDBL', 'unit': None, 'branch': 'GASA', 'cost_center': '0060 - GASA - BDBL'}, 
    # {'section': '0070 - Haa - BDBL', 'unit': None, 'branch': 'HAA MAIN', 'cost_center': '0070 - Haa Main - BDBL'}, 
    # {'section': '0080 - Chukha - BDBL', 'unit': None, 'branch': 'CHUKHA', 'cost_center': '0080 - CHUKHA - BDBL'}, 
    # {'section': '0090 - Tashigang - BDBL', 'unit': None, 'branch': 'TRASHIGANG MAIN', 'cost_center': '0090 - Trashigang Main - BDBL'}, 
    # {'section': '0100 - Tashiyangtse - BDBL', 'unit': None, 'branch': 'Tashiyangtse Main', 'cost_center': '0100 - Tyangtse Main - BDBL'}, 
    # {'section': '0110 - Mongar - BDBL', 'unit': None, 'branch': 'MONGAR MAIN', 'cost_center': '0110 - MONGAR MAIN - BDBL'},
    # {'section': '0120 - Lhuntse - BDBL', 'unit': None, 'branch': 'LHUNTSE MAIN', 'cost_center': '0120 - LHUNTSE MAIN - BDBL'}, 
    # {'section': '0130 - Samdrupjonkhar - BDBL', 'unit': None, 'branch': 'Samdrupjonkhar Main 0130', 'cost_center': '0130 - Sjongkhar Main - BDBL'}, 
    # {'section': '0140 - Pemagatsel - BDBL', 'unit': None, 'branch': 'Pemagatsel Main', 'cost_center': '0140 - Pgatshel Main - BDBL'}, 
    # {'section': '0150 - Bumthang - BDBL', 'unit': None, 'branch': 'BUMTHANG MAIN', 'cost_center': '0150 - BUMTHANG MAIN - BDBL'},  
    # {'section': '0160 - Trongsa - BDBL', 'unit': None, 'branch': 'Trongsa Main', 'cost_center': '0160 - Trongsa Main - BDBL'}, 
    # {'section': '0170 - Zhemgang - BDBL', 'unit': None, 'branch': 'ZHEMGANG MAIN', 'cost_center': '0170 - ZHEMGANG MAIN - BDBL'}, 
    # {'section': '0180 - Sarpang - BDBL', 'unit': None, 'branch': 'Sarpang', 'cost_center': '0180 - Sarpang - BDBL'}, 
    # {'section': '0190 - Dagana - BDBL', 'unit': None, 'branch': 'Dagana', 'cost_center': '0190 - Dagana - BDBL'}, 
    # {'section': '0200 - Samtse - BDBL', 'unit': None, 'branch': 'SAMTSE MAIN', 'cost_center': '0200 - SAMTSE MAIN - BDBL'}, 
    # {'section': '0210 - Tsirang - BDBL', 'unit': None, 'branch': 'Tsirang', 'cost_center': '0210 - Tsirang - BDBL'}, 
    # {'section': '0220 - Wamrong - BDBL', 'unit': None, 'branch': 'Wamrong Main', 'cost_center': '0220 - WAMRONG MAIN - BDBL'}, 
    # {'section': '0230 - Phuntsholing - BDBL', 'unit': None, 'branch': 'Phuntsholing', 'cost_center': '0230 - Phuntsholing - BDBL'}, 
    # {'section': '0240 - Nganglam - BDBL', 'unit': None, 'branch': 'Nganglam', 'cost_center': '0240 - Nganglam - BDBL'}, 
    # {'section': '0250 - Panbang - BDBL', 'unit': None, 'branch': 'Panbang', 'cost_center': '0250 - Panbang - BDBL'}, 
    # {'section': '0260 - Dorokha - BDBL', 'unit': None, 'branch': 'Dorokha', 'cost_center': '0260 - Dorokha - BDBL'}, 
    # {'section': '0270 - Jomotsangkha - BDBL', 'unit': None, 'branch': 'Jomotsangkha', 'cost_center': '0270 - Jomotsangkha - BDBL'}, 
    # {'section': '0280 - Lhamoizingkha - BDBL', 'unit': None, 'branch': 'Lhamoizingkha', 'cost_center': '0280 - Lhamoizingkha - BDBL'}, 
    # {'section': '0290 - Gelephu - BDBL', 'unit': None, 'branch': 'GELEPHU MAIN', 'cost_center': '0290 - GELEPHU MAIN - BDBL'}, 
    # {'section': '0300 - Yadi - BDBL', 'unit': None, 'branch': 'YADHI MAIN', 'cost_center': '0300 - YADHI MAIN - BDBL'}, 
    # {'section': '0310 - Dagepela - BDBL', 'unit': None, 'branch': 'Dagepela', 'cost_center': '0310 - DPELA MAIN - BDBL'}, 
    # {'section': '0320 - Samdrupcholing - BDBL', 'unit': None, 'branch': 'Samdrupcholing', 'cost_center': '0320 - Samdrupcholing - BDBL'}, 
    # {'section': '0330 - Tashicholing - BDBL', 'unit': None, 'branch': 'TASHICHOLING MAIN', 'cost_center': '0330 - TASHICHOLING MAIN - BDBL'}, 
    # {'section': '0340 - Gedu - BDBL', 'unit': None, 'branch': 'GEDU MAIN', 'cost_center': '0340 - GEDU MAIN - BDBL'}, 
    # {'section': '0350 - Gangtey - BDBL', 'unit': None, 'branch': 'GANGTEY MAIN', 'cost_center': '0350 - GANGTEY MAIN - BDBL'}, 
    {'section': 'Customer Care - BDBL', 'unit': None, 'branch': 'Banking', 'cost_center': '0000 - Banking - BDBL'}, ]
    # {'section': 'International Banking - BDBL', 'unit': None, 'branch': 'Banking', 'cost_center': '0000 - Banking - BDBL'}, 
    # {'section': 'Corporate Banking - BDBL', 'unit': None, 'branch': 'Banking', 'cost_center': '0000 - Banking - BDBL'}, 
    # {'section': 'Payment Settlement - BDBL', 'unit': None, 'branch': 'Banking', 'cost_center': '0000 - Banking - BDBL'}, 
    # {'section': 'Retail Banking - BDBL', 'unit': None, 'branch': 'Banking', 'cost_center': '0000 - Banking - BDBL'}, ]
    
    for item in section_list:
        
        for a in frappe.db.sql("""
                           select name, branch, cost_center, division, section, unit from `tabEmployee` where section="{sec}" 
                           """.format(sec=item["section"] ), as_dict=1):
            try:
                doc = frappe.get_doc("Employee",a.name)
                doc.branch = item['branch']
                doc.cost_center = item['cost_center']
                doc.save()
            
            
                print(f'name: {doc.name}  section: {doc.section} unit: {doc.unit}   branch: {doc.branch}   cost center: {doc.cost_center}')
            except:
                pass
    frappe.db.commit()
    # for item in section_list:
    #     for a in frappe.db.sql("""
    #                         select DISTINCT section, name, branch, cost_center, division, unit from `tabEmployee` 
    #                         """, as_dict=1):
    #         print(f'name: {a.name}  division: {a.section}   branch: {a.branch}   cost center: {a.cost_center}')
            

def insert_ess_role():
    count = 1
    for a in frappe.db.sql("""
                           select u.name from `tabUser` u, `tabHas Role` hr where hr.parent = u.name and u.name not like '%thimphu%' and u.name not in ('Administrator', 'Guest', 'thinley.wangmo1137@bd.bt', 'nima.wangmo@bdbl.bt', 'deki.tshomo@bdbl.bt') group by u.name
                           """,as_dict=1):
        if not frappe.db.exists("Has Role", {"parent": a.name, "role": "Employee"}):
            has_role = frappe.new_doc("Has Role")
            has_role.parent = a.name
            has_role.parenttype = "User"
            has_role.parentfield = 'roles'
            has_role.role = 'Employee'
            has_role.flags.ignore_permissions = 1
            has_role.insert()
            print(str(count)+" "+a.name)
            count += 1

def update_leave_approver():
    for a in frappe.db.sql("""
                           select name, reports_to from `tabEmployee`
                           """, as_dict=1):
        if a.reports_to:
            email = frappe.db.get_value("Employee", a.reports_to, "user_id")
            frappe.db.sql("""
                          update `tabEmployee` set expense_approver = '{}' where name = '{}'
                          """.format(email, a.name))
            print(a.name)

def update_salary_slips():
    for ss in frappe.db.sql("""
                            select name from `tabSalary Slip` where docstatus = 1
                            """,as_dict=1):
        doc = frappe.get_doc("Salary Slip", ss.name)
        doc.set_net_total_in_words()
        print(ss.name)
    frappe.db.commit()

def save_salary_structure():
    for ss in frappe.db.sql("""
                            select name from `tabSalary Structure`
                            where is_active = 'Yes'
                            """,as_dict=1):
        doc = frappe.get_doc("Salary Structure", ss.name)
        doc.save()


def update_asset_journal_entry():
    journal_entries = frappe.db.sql("""
                                    select name, title from `tabJournal Entry` where creation > '2024-02-01' and title like '%Legacy%'
                                or title like '%Accumulated%' and posting_date = '2022-12-31';
                                    """,as_dict=1)
    for je in journal_entries:
        count = 0
        fixed_asset_account = accumulated_depreciation_account = None
        je = frappe.get_doc("Journal Entry", je.name)
        gles = frappe.db.sql("""
                                    select name from `tabGL Entry` where voucher_no = '{}'
                                    """.format(je.name),as_dict=1)
        for d in je.accounts:
            if 'Legacy Clearing' not in d.account and 'Legacy Clearing' in je.title:
                fixed_asset_account = frappe.get_value("Asset Category Account", {"parent":frappe.db.get_value("Asset", d.reference_name, "asset_category")}, "fixed_asset_account")
                frappe.db.sql("""
                              update `tabJournal Entry Account` set account = '{}' where name = '{}'
                              """.format(fixed_asset_account, d.name))
                gle = frappe.db.sql("""
                                    select name from `tabGL Entry` where account not like '%Legacy Clearing%' and voucher_no = '{}'
                                    """.format(je.name),as_dict=1)
                if gle:
                    frappe.db.sql("""
                                update `tabGL Entry` set account = '{}' where name = '{}'
                                """.format(fixed_asset_account, gle[0].name))
            if 'Legacy Clearing' not in d.account and 'Accumulated' in je.title:
                accumulated_depreciation_account = frappe.get_value("Asset Category Account", {"parent":frappe.db.get_value("Asset", d.reference_name, "asset_category")}, "accumulated_depreciation_account")
                frappe.db.sql("""
                              update `tabJournal Entry Account` set account = '{}' where name = '{}'
                              """.format(accumulated_depreciation_account, d.name))
                gle = frappe.db.sql("""
                                    select name from `tabGL Entry` where account not like '%Legacy Clearing%' and voucher_no = '{}'
                                    """.format(je.name),as_dict=1)
                if gle:
                    frappe.db.sql("""
                                update `tabGL Entry` set account = '{}' where name = '{}'
                                """.format(accumulated_depreciation_account, gle[0].name))

        frappe.db.sql("""
                    update `tabJournal Entry` set posting_date = '2023-01-01' where name = '{}'
                      """.format(je.name))
        for gl in gles:
            frappe.db.sql("""
                        update `tabGL Entry` set posting_date = '2023-01-01' where name = '{}'
                        """.format(gl.name))
        print(je.name)
def save_asset():
    count = 1
    assets = frappe.db.sql("""
                        select name from `tabAsset` where docstatus = 0
                        """,as_dict=1)
    for a in assets:
        print(a.name)
        asset = frappe.get_doc("Asset", a.name)
        asset.save(ignore_permissions=1)
        if count % 100 == 0:
            frappe.db.commit()
        count += 1

def depreciate_asset():
    count=0
    for a in frappe.db.sql("""
                           select a.name, d.schedule_date
                           from `tabAsset` a inner join
                           `tabDepreciation Schedule` d
                           on a.name = d.parent
                           where d.schedule_date <= '2023-12-31'
                           and (d.journal_entry is null or d.journal_entry ='')
                           and a.status = 'Partially Depreciated'
                           """,as_dict=1):
        count+=1
        # make_depreciation_entry(a.name, a.schedule_date)

def delete_asset_related_data():
    # Fetch voucher_no values to delete
    print('STARTED')
    voucher_nos = frappe.db.sql_list("""
        SELECT je.name
        FROM `tabJournal Entry` je, `tabJournal Entry Account` jea 
        WHERE jea.parent=je.name
        AND jea.reference_type = 'Asset'
        GROUP BY je.name
        LIMIT 5000
    """)

    count=0
    
    if not voucher_nos:
        return

    voucher_no_values = ",".join(["'{}'".format(d) for d in voucher_nos])

    # Use a single SQL query to delete related data from all tables
    frappe.db.sql("""
        DELETE gl, jea, je
        FROM `tabGL Entry` gl
        LEFT JOIN `tabJournal Entry Account` jea ON jea.parent = gl.voucher_no
        LEFT JOIN `tabJournal Entry` je ON je.name = jea.parent
        WHERE gl.voucher_no IN ({})
    """.format(voucher_no_values))
    print('DONE')


def delete_cogm_gl():
    # Fetch voucher_no values to delete
    voucher_nos = frappe.db.sql_list("""
        SELECT voucher_no
        FROM `tabGL Entry`
        WHERE account = 'Cost of Goods Manufactured - SMCL' AND posting_date <= '2023-12-31'
        AND is_cancelled = 1
        AND voucher_no LIKE '%%MI%%'
        GROUP BY voucher_no
        LIMIT 1000
    """)

    print(str(voucher_nos))

    # Delete records based on voucher_no
    # count = frappe.db.sql("""
    #     DELETE FROM `tabGL Entry`
    #     WHERE voucher_no IN (%s)
    # """ % ', '.join(['%s'] * len(voucher_nos)), tuple(voucher_nos), as_dict=1)

    count = frappe.db.sql("""
        UPDATE `tabGL Entry`
        SET is_cancelled = 0
        WHERE voucher_no IN (%s)
    """ % ', '.join(['%s'] * len(voucher_nos)), tuple(voucher_nos), as_dict=1)

    print("DONE: Cancelled {} records.".format(count))

def delete_mines_inventory_gl():
    accounts = [
        'CDM Warehouse 1 - Mines - SMCL',
        'CDM Warehouse 2 - Crushing & Screen Plant - SMCL',
        'CDM Warehouse 3 - Lhamokhola Crusher - SMCL',
        'CDM Warehouse 4 - Lhamokhola Stockyard - SMCL',
        'Chunaikhola Dolomite Mine Warehouse - SMCL',
        'DSQ Warehouse 1 - Dzongthung Crusher - SMCL',
        'DSQ Warehouse 2 - Dzungdi Crusher - SMCL',
        'Habrang Coal Stockyard - SMCL',
        'Khothakpa Gypsum Mine - SMCL',
        'Majuwa Coal Warehouse - SMCL',
        'Motanga Stockyard - SMCL',
        'Rangia Stockyard - SMCL',
        'Rishore Coal Warehouse - SMCL',
        'Round Off - SMCL',
        'Samdrup Jongkhar Gypsum Stockyard - SMCL',
        'Tshophangma Coal Warehouse - SMCL'
    ]

    # Use a single SQL DELETE statement with an IN clause
    # frappe.db.sql("""
    #     DELETE FROM `tabGL Entry`
    #     WHERE account IN (%s)
    #     AND posting_date BETWEEN '2023-01-01' AND '2023-12-31'
    # """ % ', '.join(['%s'] * len(accounts)), tuple(accounts))

    frappe.db.sql("""
        UPDATE `tabGL Entry`
        SET is_cancelled = 1
        WHERE account IN (%s)
        AND posting_date BETWEEN '2023-01-01' AND '2023-12-31'
    """ % ', '.join(['%s'] * len(accounts)), tuple(accounts))

    print('DONE')

def test_bank_payment():
    # ack_file = "/home/frappe/erp/apps/erpnext/PEMSPAY_20231127_SL2023112700000003_VALERR.csv"
    # file_name = 'PEMSPAY_20231127_SL2023112700000003.csv'
    # file_status = 'Failed'
    # bank ='BOBL'
    doc = frappe.get_doc("Bank Payment", "BPO23110306")
    doc.append_bank_response_in_bpi()

#change
def update_salary_structure():
    count = 1
    ss = frappe.db.sql("""
        select ss.name, ss.employee_grade, ss.employment_type, ss.employee_group from `tabSalary Structure` ss,
        `tabEmployee` e where e.name = ss.employee
        and e.status = 'Active' and ss.is_active = 'Yes'
    """,as_dict=1)
    if ss:
        for s in ss:
            sal_struct = frappe.get_doc("Salary Structure", s.name)
            if s.employee_group not in ("Temporary"):
                sal_struct.eligible_for_fixed_allowance = 1
                sal_struct.eligible_for_cash_handling = 0
                for e in sal_struct.earnings:
                    if e.salary_component == "Basic Pay":
                        if s.employee_grade not in ("S1","S2","S3","O1","O2","O3","O4","O5","O6","O7","GS1","GS2","ESP"):
                            e.amount += e.amount * 0.02
                        else:
                            e.amount += e.amount * 0.05
                        e.amount = flt(e.amount,0)
                        e.amount = math.ceil(e.amount)
                        if flt(str(e.amount)[len(str(e.amount))-1]) > 0 and flt(str(e.amount)[len(str(e.amount))-1]) <= 5:
                            e.amount = flt(str(e.amount)[0:len(str(e.amount))-1]+"5")
                        elif flt(str(e.amount)[len(str(e.amount))-1]) > 5 and flt(str(e.amount)[len(str(e.amount))-1]) <= 9:
                            value_to_add = 10 - flt(str(e.amount)[len(str(e.amount))-1])
                            e.amount = e.amount + value_to_add
                sal_struct.save(ignore_permissions=1)
                print(str(count)+". "+sal_struct.employee)
                count += 1

def check_dn():
    doc = frappe.get_doc("Delivery Note","DN2304050001")
    doc.make_gl_entries()

def update_sle_gl():
    i = 0
    production = []
    for a in frappe.db.sql("""select name, actual_qty, incoming_rate,
                                valuation_rate, qty_after_transaction,
                                stock_value_difference, stock_value, voucher_no
                                from `tabStock Ledger Entry` 
                                where voucher_type="Production"
                                and posting_date between '2023-07-31' and '2023-08-28' 
                                and is_cancelled=0
                                order by posting_date, posting_time
                            """, as_dict=True):
        stock_value = abs(a.qty_after_transaction) * a.valuation_rate
        rate = abs(a.incoming_rate) if a.actual_qty > 0 else abs(a.valuation_rate)
        stock_value_difference = abs(a.actual_qty) * rate 
        val_diff = flt(abs(a.stock_value_difference) - stock_value_difference,2)
        val = flt(a.stock_value - stock_value,2)

        act_stock_value = stock_value if val > 1 or val < -1 else a.stock_value
        act_stock_value_diff = stock_value_difference if val_diff > 1 or val_diff < -1 else a.stock_value_difference
        if val_diff > 1 or val_diff < -1 or val > 1 or val < -1:
            i += 1
            if a.voucher_no not in production:
                production.append(a.voucher_no)
            print(i, a.voucher_no)
            frappe.db.sql("""  update `tabStock Ledger Entry`
                set stock_value='{}', stock_value_difference='{}'
                where name ='{}'
            """.format(act_stock_value, act_stock_value_diff, a.name))
    j=0
    for b in production:
        j+=1
        print(j, b, i)
        frappe.db.sql("delete from `tabGL Entry` where voucher_type='Production' and voucher_no='{}'".format(b))
        doc = frappe.get_doc("Production", b)
        doc.make_gl_entries()
        print("Done for Production No: " + str(b))
    frappe.db.commit()

def correct_dn():
    for b in ("DN2302070020",):
        frappe.db.sql("delete from `tabGL Entry` where voucher_type='Delivery Note' and voucher_no='{}'".format(b))
        for a in frappe.db.sql("""select name, actual_qty, incoming_rate,
                                    valuation_rate, qty_after_transaction
                                    from `tabStock Ledger Entry` 
                                    where voucher_no="{}"
                                """.format(b), as_dict=True):
            stock_value = a.qty_after_transaction * a.valuation_rate
            stock_value_difference = a.actual_qty * a.incoming_rate
            
            frappe.db.sql("""  update `tabStock Ledger Entry`
                            set stock_value='{}', stock_value_difference='{}'
                            where name ='{}'
                        """.format(stock_value, stock_value_difference, a.name))
            
        doc = frappe.get_doc("Delivery Note", b)
        doc.make_gl_entries()
        frappe.db.commit()
        print("Done for DN No: " + str(b))


def get_wrong_dn():
    i=0
    for a in frappe.db.sql("""
                    select is_cancelled docstatus, voucher_no, credit, posting_date, account from `tabGL Entry`
                    where voucher_type="Delivery Note"
                    and account="Cost of Goods Manufactured - SMCL"
                    and credit > 0
                    and is_cancelled = 0
                    order by posting_date 
                """, as_dict=True):
        i+=1
        print(str(i) + ", " + str(a.voucher_no))

def rename_pr():
    pr_name = "HR-PRUN-2025-00004"
    rename_to = "HR-PRUN-2024-00041"
    import frappe.model.rename_doc as rd
    rd.rename_doc("Payroll Entry", pr_name, rename_to, force=True)

        
def rename_asset():
    i = 0
    abbr = "SMCL-BCS-23-"
    for d in frappe.db.sql("select name, asset_category, creation from `tabAsset` \
            where asset_category in ('Building & Civil Structure') and docstatus = 0 order by creation",as_dict=True):
        name  = ""
        if len(str(i)) == 1:
            name = abbr +"000"+ str(i)
        elif len(str(i)) == 2:
            name = abbr +"00"+ str(i)
        elif len(str(i)) == 3:
            name = abbr +"0"+ str(i)
        else:
            name = abbr + str(i)
            
        print(name)
        i += 1
def delete_asset_gl():
    for d in frappe.db.sql("select name, asset_category from `tabAsset` \
            where asset_category in ('Furniture & Fixture', 'Plant & Machinery','Building & Civil Structure') and docstatus = 2",as_dict=True):
        frappe.db.sql("delete from `tabGL Entry` where against_voucher_type='Asset' and against_voucher= '{}'".format(d.name))
        for je in frappe.db.sql("select distinct(parent) as name from `tabJournal Entry Account` where reference_name= '{}'".format(d.name),as_dict=1):
            je_doc = frappe.get_doc("Journal Entry",je.name)
            print(je_doc.name)
            je_doc.delete()
    #     asset = frappe.get_doc("Asset",d.name)
    #     print(asset.name, ' ',asset.asset_category,' ', asset.docstatus)
    #     asset.cancel()
    print("Done")
    frappe.db.commit()
def detete_pol_receive_gl():
    name = frappe.db.sql("""select name
            from `tabPOL Receive`
            where direct_consumption=1
            and use_common_fuelbook =1
            and is_opening =0
            and docstatus=1
        """,as_dict=True)
    for x in name:
        frappe.db.sql("delete from `tabGL Entry` where against_voucher_type='POL Receive' and against_voucher= '{}'".format(x.name))
        print(x.name)
def pol_issue_double_equipment_issue():
    from_date = '01-01-2023'
    to_date = '11-10-2023'
    name=frappe.db.sql("""
            select name
            from `tabPOL Issue`
            where docstatus =1
            and posting_date between '{0}' and '{1}'
        """.format(from_date, to_date),as_dict=True)
    print(name)
def create_pol_receive_gl():
    name = frappe.db.sql("""select name
            from `tabPOL Receive`
            where direct_consumption=1
            and use_common_fuelbook =1
            and is_opening =0
            and docstatus=1
        """,as_dict=True)
    for x in name:
        gl_entry = frappe.db.sql("select name from `tabGL Entry` where against_voucher_type='POL Receive' and against_voucher= '{}'".format(x.name))
        if gl_entry:
            print(gl_entry)
        else:
            doc = frappe.get_doc("POL Receive",x.name)
            doc.make_gl_entries()
            print(doc.name)
    frappe.db.commit()

def pol_entry_correction():
    for d in frappe.bd.sql("select name,reference_type,reference,equipment from `tabPOL Entry` where rate <= 0"):
        if d.reference_type == "POL Receive":
            doc = frappe.get_doc(d.reference_type,d.reference)
            if doc.name:
                frappe.db.sql('''
                    update `tabPOL Entry` set fuelbook = '{}', supplier='{}', item_name='{}',
                    memo_number = '{}', pol_slip_no = '{}', mileage = '{}', km_difference = '{}',
                    current_km = '{}', rate = {} where name = '{}'
                    '''.format(doc.fuelbook,doc.supplier,doc.item_name, doc.memo_number, 
                doc.pol_slip_no, doc.mileage, doc.km_difference, doc.cur_km_reading, doc.rate, d.name))
        elif d.reference_type == "POL Issue":
            doc = frappe.get_doc("POL Issue Items",{"parent":d.reference,"equipment":d.equipment})
            if doc.name:
                frappe.db.sql('''
                    update `tabPOL Entry` set fuelbook = '{}', mileage = '{}', km_difference = '{}',
                    current_km = '{}', rate = {} where name = '{}' and equipment = '{}'
                    '''.format(doc.fuelbook, doc.mileage, doc.km_difference, doc.cur_km_reading, doc.rate, d.name, doc.equipment))
    
def cost_center_correction_budget():
    for d in frappe.db.get_list("Committed Budget",filters={"reference_type":"Journal Entry"},fields=["cost_center","name"]):
        parent_cost_center = frappe.db.get_value("Cost Center",{"name":d.cost_center,"use_budget_from_parent":1},["budget_cost_center"])
        if parent_cost_center:
            frappe.db.sql("update `tabCommitted Budget` set cost_center = '{}' where name = '{}'".format(parent_cost_center,d.name))
            print(d.cost_center,' ',d.name)
    print('<===================================================>')
    for d in frappe.db.get_list("Consumed Budget",filters={"reference_type":"Journal Entry"},fields=["cost_center",'name']):
        parent_cost_center = frappe.db.get_value("Cost Center",{"name":d.cost_center,"use_budget_from_parent":1},["budget_cost_center"])
        if parent_cost_center:
            frappe.db.sql("update `tabConsumed Budget` set cost_center = '{}' where name = '{}'".format(parent_cost_center,d.name))
            print(parent_cost_center,' ',d.name)
    print('done')
    frappe.db.commit()

def create_gl_for_previous_production():
    for p in frappe.db.get_list("Production",filters={"creation":["<=","2023-03-02"],"docstatus":1}, fields=["name","creation"]):
        doc = frappe.get_doc("Production",p.name)
        if len(doc.raw_materials) > 0:
            frappe.db.sql("delete from `tabGL Entry` where voucher_no = '{}' and voucher_type = 'Production'".format(doc.name))
            doc.make_gl_entries()
            print(doc.name)
    frappe.db.commit()
    print('done')
def create_leave_ledger_entry():
    for e in frappe.db.sql('''select name from `tabEmployee` where status = "Active"''',as_dict=1):
        if frappe.db.exists("Leave Allocation",{"employee":e.name,"leave_type":"Earned Leave","docstatus":1}):
            leave_allocation = frappe.get_doc("Leave Allocation",{"employee":e.name,"leave_type":"Earned Leave","docstatus":1})
            print(leave_allocation.employee, ' : ', leave_allocation.name, ' : ', leave_allocation.leave_type)
            leave_ledger_entry = frappe.new_doc("Leave Ledger Entry")
            leave_ledger_entry.flags.ignore_permissions=1
            leave_ledger_entry.update({
                "employee":leave_allocation.employee,
                "employee_name":leave_allocation.employee_name,
                "leave_type":leave_allocation.leave_type,
                "transaction_type":"Leave Allocation",
                "transaction_name":leave_allocation.name,
                "leaves":2.5,
                "company":leave_allocation.company,
                "from_date":"2023-01-01",
                "to_date":'2023-12-31'
            })
            leave_ledger_entry.insert()
            leave_ledger_entry.submit()

# def post_payment_je_leave_encashment():
#     le = frappe.db.sql("""
#         select expense_claim from `tabLeave Encashment` where
#         docstatus = 1
#     """,as_dict=1)
#     for a in le:
#         expense_claim = frappe.get_doc("Expense Claim", a.expense_claim)
#         if expense_claim.docstatus = 1:
#             expense_claim.post_accounts_entry()
#             print(expense_claim.name)
#     frappe.db.commit()

def change_account_name():
    # print('here')
    for d in        [
                    {
                    "old_name": "Tshophhangma Consumable Warehouse",
                    "new_name": "Tshophangma Consumable Warehouse - SMCL"
                    }
                    ]:
        if frappe.db.exists("Account",{"account_name":d.get("old_name")}):
            doc = frappe.get_doc("Account",{"account_name":d.get("old_name")})
            print('old : ',doc.account_name,'\nNew Name : ' ,d.get("new_name"))
            doc.account_name = d.get("new_name")
            doc.save()

def assign_je_in_invoice():
    print('<------------------------------------------------------------------------------------------------>')
    for d in frappe.db.sql('''
                select reference_name, reference_type, parent from `tabJournal Entry Account` where reference_type in ('Transporter Invoice','EME Invoice')
                ''', as_dict=True):
        if d.reference_type and d.reference_name and frappe.db.exists(d.reference_type, d.reference_name):
            doc = frappe.get_doc(str(d.reference_type),str(d.reference_name))
            doc.db_set("journal_entry",d.parent)
    print('Done')
def assign_ess_role():
    users = frappe.db.sql("""
        select name from `tabUser` where name not in ('Guest', 'Administrator')
    """,as_dict=1)
    for a in users:
        user = frappe.get_doc("User", a.name)
        user.flags.ignore_permissions = True
        if "Employee Self Service" not in frappe.get_roles(a.name):
            user.add_roles("Employee Self Service")
            print("Employee Self Service role added for user {}".format(a.name))


def delete_salary_detail_salary_slip():
    ssd = frappe.db.sql("""
        select name from `tabSalary Detail` where parenttype = 'Salary Slip'
    """,as_dict=1)
    for a in ssd:
        frappe.db.sql("delete from `tabSalary Detail` where name = '{}'".format(a.name))
        print(a.name)

def create_users():
    print("here")

    employees = frappe.db.sql("""
        select name from `tabEmployee` where company_email is not NULL and user_id is NULL
    """,as_dict=1)
    if employees:
        for a in employees:
            employee = frappe.get_doc("Employee", a.name)
            if not frappe.db.exists("User",employee.company_email):
                create_user(a.name, email = employee.company_email)
                print("User created for employee {}".format(a.name))
                employee.db_set("user_id", employee.company_email)
    frappe.db.commit()

def update_employee_user_id():
    print()
    users = frappe.db.sql("""
        select name from `tabUser`
    """,as_dict=1)
    if users:
        for a in users:
            employee = frappe.db.get_value("Employee",{"company_email":a.name},"name")
            if employee:
                employee_doc = frappe.get_doc("Employee",employee)
                employee_doc.db_set("user_id",a.name)
                print("Updated email for "+str(a.name))
    frappe.db.commit()

def update_benefit_type_name():
    bt = frappe.db.sql("""
        select name, benefit_type from `tabEmployee Benefit Type`;
    """, as_dict=True)
    if bt:
        for a in bt:
            frappe.db.sql("update `tabEmployee Benefit Type` set name = '{}' where name = '{}'".format(a.benefit_type, a.name))
            print(a.name)

def update_department():
    el = frappe.db.sql("""
        select name from `tabEmployee`
        where department = 'Habrang & Tshophangma Coal Mine - SMCL'
        and status = 'Active'
    """,as_dict=1)
    if el:
        for a in el:
            frappe.db.sql("""
                update `tabEmployee` set department = 'PROJECTS & MINES DEPARTMENT - SMCL'
                where name = '{}'
            """.format(a.name))
            print(a.name)

def update_user_pwd():
    user_list = frappe.db.sql("select name from `tabUser` where name not in ('Administrator', 'Guest')", as_dict=1)
    c = 1
    non_employee = []
    for i in user_list:
        print("NAME '{}':  '{}'".format(c,str(i.name)))
        if not frappe.db.exists("Employee", {"user_id":i.name}):
            non_employee.append({"User ID":i.name, "User Name":frappe.db.get_value("User",i.name,"full_name")})
        ds = frappe.get_doc("User", i.name)
        ds.new_password = 'smcl@2022'
        ds.save(ignore_permissions=1)
        c += 1
    # df = pd.DataFrame(data = non_employee) # convert dict to dataframe
    # df.to_excel("Users Without Employee Data.xlsx", index=False)
    # print("Dictionery Converted in to Excel")

def update_ref_doc():
    for a in frappe.db.sql("""
                            select name 
                            from 
                                `tabExpense Claim` 
                            where 
                                docstatus != 2
                            """):
        print(a[0])
        reference = frappe.db.sql("""
                            select expense_type
                            from 
                                `tabExpense Claim Detail` 
                            where 
                            parent = "{}"
                            """.format(a[0]))
        print(reference[0][0])
        frappe.db.sql("""
            update 
                `tabExpense Claim`
            set ref_doc ="{0}"
            where name ="{1}"
        """.format(reference[0][0],a[0]))

    
def update_overtime_application_in_ss():
    with open("/home/frappe/erp/apps/Overtime.csv") as f:
        reader = csv.reader(f)
        mylist = list(reader)
        c = 0
        for i in mylist:
            ss = frappe.db.sql("select name, employee, employee_name, branch, is_active from `tabSalary Structure` where employee='{}'and name='{}'".format(i[1], i[0]), as_dict=1)        
            for d in ss:
                ss_doc = frappe.get_doc("Salary Structure", {"name": d.name})
                if ss_doc.employee == i[1]:
                    row = ss_doc.append('earnings',{})
                    row.salary_component = "Overtime Allowance"
                    row.amount = flt(i[3])
                    row.from_date = "2023-04-01"
                    row.to_date = "2023-04-30"
                ss_doc.save(ignore_permissions=True)
                
                # rem_list = []
                # for a in ss_doc.get("earnings"):
                #     if ss_doc.employee == i[1] and a.salary_component == "Overtime Allowance":
                #         rem_list.append(a)

                # [ss_doc.remove(a) for a in rem_list]
                # ss_doc.save(ignore_permissions=True)
            c += 1
        print('DONE')
        print(str(c))


def earned_leave_deletion_manual():
    count=0
    for d in frappe.db.sql("select name, employee, from_date, leaves, transaction_name from `tabLeave Ledger Entry` where from_date='2023-06-21'", as_dict=1):
        # print(str(d.transaction_name))    
        # print(str(d.from_date))    
        leave_all = frappe.get_doc("Leave Allocation", d.transaction_name)
        leave_all.total_leaves_allocated = flt(leave_all.total_leaves_allocated) - flt(2.5)
        leave_all.save(ignore_permissions=True)
        frappe.db.sql("delete from `tabLeave Ledger Entry` where from_date='2023-06-21' and name='{}'".format(d.name))
        count+=1
    print(str(count))

# def update_sales_target():
#     name= frappe.db.sql(""" 
#             select name from `tabSales Target Item` where parent="Dolomite-2022-2036"
#         """)
#     frappe.print(str(name))
