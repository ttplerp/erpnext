import oracledb
import frappe
from frappe.model.document import Document
from datetime import datetime
from frappe.utils import nowdate, cint, flt, getdate

def decode_string(input_str):
    # Decode from 'latin1' to 'utf-8' and remove any null bytes (\x00)
    return input_str.encode('latin1').decode('utf-8').replace('\x00', '')

def get_db_connection():
    try:
        #Database credentials
        user = 'custom' #'bdb1150'
        password = 'custom' #'bdb2025'
        dsn = '172.20.2.13:1521/bdblfcdb'
        conn = oracledb.connect(user=user, password=password, dsn=dsn)
        return conn
    except oracledb.DatabaseError as e:
        print("Connection failed:", e)

def cbs_statement_query(acc_no=None, from_date=None, to_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
       SELECT 
            tran_particular, 
            tran_rmks, 
            TO_CHAR(entry_date,'YYYY-MM-DD HH24:MI:SS') AS tran_date, 
            ref_amt, 
            part_tran_type, 
            tran_id
        FROM tbaadm.htd 
        WHERE acid IN (SELECT acid FROM tbaadm.gam WHERE foracid='{0}') 
        AND tran_date BETWEEN TO_DATE('{1}', 'YYYY-MM-DD') AND TO_DATE('{2}', 'YYYY-MM-DD')
        UNION
        SELECT 
            tran_particular, 
            tran_rmks, 
            TO_CHAR(entry_date,'YYYY-MM-DD HH24:MI:SS') AS tran_date, 
            ref_amt, 
            part_tran_type,
            tran_id
        FROM tbaadm.dtd 
        WHERE acid IN (SELECT acid FROM tbaadm.gam WHERE foracid='{0}')
        AND tran_date BETWEEN TO_DATE('{1}', 'YYYY-MM-DD') AND TO_DATE('{2}', 'YYYY-MM-DD')
        ORDER BY tran_date ASC
    """.format(acc_no, from_date, to_date))
    result = cursor.fetchall()
    import re
    record = []
    for a in result:
        # - Match numbers with at least 12 digits
        # - Appearing at:
        #   - start of line followed by /
        #   - between slashes (/number/)
        #   - near end, followed by space, slash, or line end
        pattern = r"(?:^|/)(\d{12,})(?=/|\s|$)"
        matches = re.findall(pattern, a[0])
        rr_no = ' '.join(matches)  # Assuming the only single RR No in Remarks

        #print(str(rr_no), a[0], a[2])
        record.append({
            "ref_no":rr_no, 
            "tran_particular": a[0], 
            "tran_rmks": a[1], 
            "trans_date": a[2], 
            "amount":a[3], 
            "debit_credit":a[4],
            "tran_id": a[5],
        })
    return record

@frappe.whitelist()
def cbs_loan_enquiry(account_no=None):
    #754000765101
    if account_no:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
           select 
            gam.acct_name, gam.foracid, gam.SANCT_LIM as Disbursement_amount, gam.CLR_BAL_AMT*-1 as Loan_Balance,
            gam.acct_opn_date, eit.interest_rate*-1 as interest_rate,
            lrs.flow_amt as Installment_amt, lrs.LR_FREQ_TYPE as Repayment_Frequency,
            lrs.NEXT_DMD_DATE as Next_Installment_Date, 
            (lrs.num_of_flows-lrs.num_of_dmds)as Installment_Remaining, lam.EI_PERD_END_DATE as Maturity_date,
            accounts.nat_id_card_num, gam.cif_id
            from tbaadm.gam, crmuser.accounts, tbaadm.eit,tbaadm.lam,tbaadm.lrs
            where gam.acid=eit.entity_id
            and gam.cif_id=accounts.orgkey
            and eit.entity_id=lam.acid
            and lam.acid=lrs.acid
            and (gam.foracid='{0}' or accounts.nat_id_card_num='{0}')
        """.format(account_no))

        result = cursor.fetchall()
        record = []
        if result:
            for a in result:
                record.append(
                        {
                        "account_holder": a[0], 
                        "account_no": a[1], 
                        "total_loan":a[2],
                        "loan_balance": a[3],
                        "loan_avail_date": a[4].strftime("%d-%b-%Y"),
                        "interest_rate": a[5],
                        "installment_amount": a[6],
                        "repayment_frequency": a[7],
                        "next_payment_date": a[8].strftime("%d-%b-%Y"),
                        "maturity_date": a[10].strftime("%d-%b-%Y"),
                        "balance_installment": a[9],
                        "cid": a[11],
                        "cif": a[12]
                    })
            return record

@frappe.whitelist()
def trial_balance_check(sol_id=None, report_date=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cond = ""
    if sol_id:
        cond =  """ and tbaadm.gam.sol_id in (select sol_id from tbaadm.SST where set_id = upper('{0}'))""".format(sol_id)

    cursor.execute("""
               SELECT  SOL_ID,SUM(DEBITS), SUM(CREDITS), SUM(DEBITS)-SUM(CREDITS) FROM (    
SELECT 
        TBAADM.GAM.SOL_ID,
        TBAADM.GSH.GL_SUB_HEAD_CODE,
        TBAADM.GSH.GL_SUB_HEAD_DESC,FORACID,
        sum(abs((case when TBAADM.EAB.tran_DATE_BAL < 0 then TBAADM.EAB.tran_DATE_BAL else 0 end))) as debits,
        sum(abs((case when TBAADM.EAB.tran_DATE_BAL >= 0 then TBAADM.EAB.tran_DATE_BAL else 0 end))) as credits
FROM  TBAADM.GAM,TBAADM.GSH,TBAADM.EAB
where to_date('{report_date}','YYYY-MM-DD') between TBAADM.EAB.EOD_DATE  AND  TBAADM.EAB.END_EOD_DATE
{cond} 
and TBAADM.EAB.EOD_DATE is not null
and TBAADM.EAB.END_EOD_DATE is not null
and tbaadm.gam.sol_id=tbaadm.gsh.sol_id
AND TBAADM.GSH.CRNCY_CODE=TBAADM.GAM.ACCT_CRNCY_CODE
and tbaadm.gam.ACID=tbaadm.EAB.ACID
AND TBAADM.GAM.GL_SUB_HEAD_CODE= TBAADM.GSH.GL_SUB_HEAD_CODE
group by         
        TBAADM.GSH.GL_SUB_HEAD_CODE,FORACID,
        TBAADM.GSH.GL_SUB_HEAD_DESC,TBAADM.GAM.SOL_ID ORDER BY TBAADM.GSH.GL_SUB_HEAD_CODE ) GROUP BY SOL_ID
            """.format(report_date=report_date, cond=cond))
    result = cursor.fetchall()    
    i=0
    record = []
    if result:
        for a in result:
            record.append({
                "sol_id": a[0],
                "debit": a[1],
                "credit": a[2],
                "variance": a[3],
            })
    return record

@frappe.whitelist()
def create_scheduler():
    # Create `Scheduled Job Type`
    job = frappe.new_doc("Scheduled Job Type")
    job.frequency = "Cron"
    job.method = "crm.cbs_db.notify_expired_cid"
    job.cron_format = "0 0 * * *"     # runs once a day and in the midnight
    job.save()

@frappe.whitelist()
def notify_expired_cid():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
                SELECT g.foracid, g.acct_name, g.schm_code, g.acct_opn_date, g.acct_cls_flg,
                    a.nat_id_card_num, e.DOCISSUEDATE AS issue, 
                    e.DOCEXPIRYDATE AS expiry, p.phoneno
                FROM 
                tbaadm.gam g,
                crmuser.accounts a,
                crmuser.entitydocument e,
                crmuser.phoneemail p
                WHERE 
                g.cif_id = a.orgkey
                AND g.schm_type in ('SBA','CAA') 
                AND a.orgkey = e.orgkey 
                AND e.orgkey = p.orgkey
                AND e.DOCEXPIRYDATE = TRUNC(SYSDATE) + 15
                AND g.acct_cls_flg = 'N'
            """)
    result = cursor.fetchall()
    i=0

    for a in result:
        msg="""Your CID/ID will expire on {}. Please update by visiting the nearest Branch or via kyc.bdb.bt before expiry date to avoid transaction restrictions""".format(str(a[7]).split(" ")[0])
        mobile_no = str(a[8])
        dtl = frappe.db.sql("""
                            select name from `tabExpired CID Notification`
                            where document_expiry_date='{}'
                            and document_id='{}'
                            and account_no='{}'
                """.format(str(a[7]).split(" ")[0], a[5], str(a[0])), as_dict=True)
        if not dtl:
            doc = frappe.new_doc("Expired CID Notification")
            doc.account_no = str(a[0])
            doc.mobile_no = mobile_no[-8:]
            doc.message = msg
            doc.document_expiry_date = str(a[7]).split(" ")[0]
            doc.document_id = a[5]
            doc.save()
            #print(str(a[0]), i, mobile_no[-8:], msg)
            i+=1

    for b in frappe.db.sql("""
                            select name, mobile_no, document_expiry_date, message
                            from `tabExpired CID Notification`
                            where sms_sent=0
                            AND (mobile_no LIKE '17%' OR mobile_no LIKE '77%' OR mobile_no LIKE '16%');
                """, as_dict=True):
        send_sms(msg, mobile_no[-8:])
        frappe.db.sql(""" update `tabExpired CID Notification` set sms_sent=1 where name='{}' """.format(b.name))
        frappe.db.commit()
        print("Send SMS", b.mobile_no, b.document_expiry_date, b.message)
            

@frappe.whitelist()
def cbs_td_enquiry(account_no=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
           select 
            gam.foracid, gam.acct_name, gsp.SCHM_DESC as Deposit_Type, tam.DEPOSIT_PERIOD_MTHS as Term_Period_In_Months, tam.OPEN_EFFECTIVE_DATE,
            tam.MATURITY_DATE, tam.DEPOSIT_AMOUNT, eit.interest_rate, tam.MATURITY_AMOUNT,
            tam.CUMULATIVE_INT_CREDITED as interest_paid_AsOfDate,
            tam.CUMULATIVE_NRML_INSTL_PAID as Installment_Paid_AsOfDate, gam.cif_id, accounts.nat_id_card_num
            from tbaadm.tam,tbaadm.gam, crmuser.accounts,tbaadm.eit,tbaadm.gsp
            where tam.acid=gam.acid
            and gam.cif_id=accounts.orgkey and gam.acid=eit.entity_id
            and gam.schm_code=gsp.schm_code and gam.acct_cls_flg='N'
            and gam.schm_type='TDA'
            AND (accounts.nat_id_card_num='{0}' or gam.foracid='{0}')
            """.format(account_no))
    result = cursor.fetchall()
    record = []
    if result:
        for a in result:
            record.append({
                "account_no": a[0],
                "account_holder": a[1],
                "deposit_type": a[2],
                "period_in_months": a[3],
                "open_date": a[4],
                "maturity_date": a[5],
                "deposit_amount": a[6],
                "interest_rate": a[7],
                "maturity_amount": a[8],
                "interest_paid": a[9],
                "installment_paid": a[10],
                "cif": a[11],
                "cid": a[12]
            })
    return record
