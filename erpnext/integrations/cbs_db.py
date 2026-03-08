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

@frappe.whitelist()
def cbs_account_enquiry(account_no=None):
    if account_no:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                g.cif_id as cif,
                a.nat_id_card_num,
                g.foracid as account_number,
                g.clr_bal_amt as balance,
                g.acct_name as name,
                LISTAGG(p.PHONENOLOCALCODE, ', ') WITHIN GROUP (ORDER BY p.PHONENOLOCALCODE) AS PHONENOLOCALCODE,
                LISTAGG(p.email, ', ') WITHIN GROUP (ORDER BY p.email) AS email,
                s.ACCT_STATUS as status,
                g.Schm_code as scheme_type
            FROM
                tbaadm.gam g
            JOIN
                tbaadm.smt s ON s.acid = g.acid
            JOIN
                crmuser.phoneemail p ON p.orgkey = g.cif_id
            JOIN
                crmuser.accounts a on a.orgkey = g.cif_id
            WHERE
                (g.foracid='{0}' or a.nat_id_card_num='{0}')
                and g.acct_cls_flg = 'N'
                and g.schm_type in ('SBA','CAA')
            GROUP BY
            g.cif_id, a.nat_id_card_num, g.foracid, g.clr_bal_amt, g.acct_name, s.ACCT_STATUS, g.Schm_code
        """.format(account_no))

        result = cursor.fetchall()
        records = []
        for a in result:
            acc_type=None
            if "OD" in a[8]:
                acc_type = "OD"
            elif "CA" in a[8]:
                acc_type = "CA"
            else:
                acc_type = "SBA"

            records.append({
                "cif":a[0],
                "cid":a[1],
                "account_no":a[2],
                "account_holder":a[4],
                "balance": a[3],
                "mobile_no":decode_string(a[5]) if a[5] else None,
                "email": decode_string(a[6]) if a[6] else None,
                "status": "Active" if a[7] == "A" else "Dormant",
                "scheme_type": acc_type,
            })
        return records
