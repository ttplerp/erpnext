import frappe
from erpnext.setup.doctype.employee.employee import create_user
import csv
from frappe.utils import flt, cint, nowdate, getdate, formatdate
import math

from erpnext.integrations.bps import process_files
from erpnext.assets.doctype.asset.depreciation import make_depreciation_entry

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
    print(str(count))

def change_asset_status():
    count=0
    for d in frappe.db.sql("select name from `tabAsset` where docstatus=0 and posting_date <='2023-12-31'", as_dict=1):
        # frappe.db.sql("update `tabAsset Finance Book` set docstatus=0 where parent='{}'".format(d.name))
        # frappe.db.sql("update `tabDepreciation Schedule` set docstatus=0 where parent='{}'".format(d.name))
        # frappe.db.sql("update `tabAsset` set docstatus=0 where name='{}'".format(d.name))

        # frappe.db.sql("delete from `tabAsset Finance Book` where parent='{}'".format(d.name))
        # frappe.db.sql("delete from `tabDepreciation Schedule` where parent='{}'".format(d.name))
        # frappe.db.sql("delete from `tabAsset` where name='{}'".format(d.name))
        count+=1
    print(str(count))

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
