from __future__ import unicode_literals
import xml.etree.ElementTree as ET
import frappe
import requests, base64
import ssl
from io import BytesIO
import pycurl
from OpenSSL import SSL
import socket
from xml.etree import ElementTree
from frappe import _
from frappe.utils import cint, flt, get_bench_path, get_datetime, today
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context
from http.client import HTTPConnection  # py3
import http.client
from urllib.request import urlopen
import os
import logging
import traceback
import json

@frappe.whitelist()
def loan_account_inq(account_no=None):
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    # url = "https://was1-dc-srv.bdbl.bt:11300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    c.setopt(c.TIMEOUT, 500)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    payload="""<?xml version="1.0" encoding="UTF-8"?>
<FIXML xsi:schemaLocation="http://www.finacle.com/fixml executeFinacleScript.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Header>
<RequestHeader>
<MessageKey>
<RequestUUID>545317899999</RequestUUID>
<ServiceRequestId>executeFinacleScript</ServiceRequestId>
<ServiceRequestVersion>10.2</ServiceRequestVersion>
<ChannelId>COR</ChannelId>
<LanguageId></LanguageId>
</MessageKey>
<RequestMessageInfo>
<BankId>01</BankId>
<TimeZone></TimeZone>
<EntityId></EntityId>
<EntityType></EntityType>
<ArmCorrelationId></ArmCorrelationId>
<MessageDateTime>2023-00-20T10:54:27.198</MessageDateTime>
</RequestMessageInfo>
<Security>
<Token>
<PasswordToken>
<UserId></UserId>
<Password></Password>
</PasswordToken>
</Token>
<FICertToken></FICertToken>
<RealUserLoginSessionId></RealUserLoginSessionId>
<RealUser></RealUser>
<RealUserPwd></RealUserPwd>
<SSOTransferToken></SSOTransferToken>
</Security>
</RequestHeader>
</Header>
<Body>
<executeFinacleScriptRequest>
<ExecuteFinacleScriptInputVO>
<requestId>loan.scr</requestId>
</ExecuteFinacleScriptInputVO>
<executeFinacleScript_CustomData>
<AcctId>{0}</AcctId>
</executeFinacleScript_CustomData>
</executeFinacleScriptRequest>
</Body>
</FIXML>""".format(account_no)

    headers = {
    'Content-Type': 'application/'
    'xml'
    }

    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    c.setopt(c.POSTFIELDS, payload)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    http_code = c.getinfo(c.RESPONSE_CODE)
    body = buffer.getvalue()
    result = str(body.decode('utf-8'))
    try:
        root = ET.fromstring(result)
        namespace = {'ns': 'http://www.finacle.com/fixml'}
        account_no = root.find('.//ns:AccountNumber', namespaces=namespace).text
        acc_holder = root.find('.//ns:AccountName', namespaces=namespace).text
        sanction_date = root.find('.//ns:sanction_date', namespaces=namespace).text
        acc_status = root.find('.//ns:ACCT_STATUS', namespaces=namespace).text
        interest_rate = root.find('.//ns:interest_rate', namespaces=namespace).text
        principal_os = root.find('.//ns:principal_OS', namespaces=namespace).text
        overdue_amt = root.find('.//ns:Overdue_Amt', namespaces=namespace).text
        outstanding_amt = root.find('.//ns:Total_Outstanding', namespaces=namespace).text
        next_payment_date = root.find('.//ns:NEXT_DMD_DATE', namespaces=namespace).text 
        emi_amt = root.find('.//ns:installment_Amount', namespaces=namespace).text
        
        #dt = datetime.strptime(sanction_date, "%Y-%m-%dT%H:%M:%S.%f")
        #sanction_date = dt.strftime("%d-%m-%Y")

        #dt = datetime.strptime(next_payment_date, "%Y-%m-%dT%H:%M:%S.%f")
        #next_payment_date = dt.strftime("%d-%m-%Y")
         
        acc_dtl = {
            "account_no": account_no,
            "acc_holder": acc_holder,
            "sanction_date": sanction_date,
            "account_status": acc_status,
            "interest_rate": interest_rate,
            "principal_os": principal_os,
            "overdue_amt": overdue_amt,
            "outstanding_amt": outstanding_amt,
            "next_payment_date": next_payment_date,
            "emi_amt": emi_amt
        }
        return acc_dtl
    except:
        return {"msg":"No Account Found"}
    c.close

@frappe.whitelist()
def account_inq(account_no=None, uuid=None, posting_date=None):
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    # url = "https://was1-dc-srv.bdbl.bt:11300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    # Optionally set a timeout
    c.setopt(c.TIMEOUT, 500)
    # Set SSL version to use TLS (if required)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    # Set the write data buffer
    c.setopt(c.WRITEDATA, buffer)
    # Follow redirects if needed
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    payload = """<FIXML xsi:schemaLocation="http://www.finacle.com/fixml AcctInq.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<Header>
		<RequestHeader>
			<MessageKey>
				<RequestUUID>7779100066</RequestUUID>
				<ServiceRequestId>AcctInq</ServiceRequestId>
				<ServiceRequestVersion>10.2</ServiceRequestVersion>
				<ChannelId>COR</ChannelId>
				<LanguageId/>
			</MessageKey>
			<RequestMessageInfo>
				<BankId>01</BankId>
				<TimeZone/>
				<EntityId/>
				<EntityType/>
				<ArmCorrelationId/>
				<MessageDateTime>2025-01-09T05:56:07.000</MessageDateTime>
			</RequestMessageInfo>
			<Security>
				<Token>
					<PasswordToken>
						<UserId/>
						<Password/>
					</PasswordToken>
				</Token>
				<FICertToken/>
				<RealUserLoginSessionId/>
				<RealUser/>
				<RealUserPwd/>
				<SSOTransferToken/>
			</Security>
		</RequestHeader>
	</Header>
	<Body>
		<AcctInqRequest>
			<AcctInqRq>
				<AcctId>
					<AcctId>{account_no}</AcctId>
				</AcctId>
			</AcctInqRq>
		</AcctInqRequest>
	</Body>
</FIXML>""".format(account_no=account_no)

    headers = {
    'Content-Type': 'application/'
    'xml'
    }

    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    # Set the POST fields (SOAP body)
    c.setopt(c.POSTFIELDS, payload)
    # Set the write data buffer
    c.setopt(c.WRITEDATA, buffer)
    # Perform the request
    try:
        c.perform()
        # Get HTTP response code
        http_code = c.getinfo(c.RESPONSE_CODE)
        # Get the response body
        body = buffer.getvalue()
        result = str(body.decode('utf-8'))
        #print(result)
        
        if result:
            root = ET.fromstring(result)
            # Define the namespace
            namespace = {'ns': 'http://www.finacle.com/fixml'}
            status = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
            if status == "SUCCESS":
                schm_type = root.find(".//ns:SchmType", namespaces=namespace).text
                cust_id = root.find(".//ns:CustId/ns:CustId", namespaces=namespace).text
                account_no = root.find(".//ns:AcctId/ns:AcctId", namespaces=namespace).text
                acc_holder = root.find(".//ns:CustId/ns:PersonName/ns:Name", namespaces=namespace).text
                prefix = root.find(".//ns:CustId/ns:PersonName/ns:TitlePrefix", namespaces=namespace).text
                acc_opening_date = root.find(".//ns:AcctOpenDt", namespaces=namespace).text
                account_status = root.find(".//ns:BankAcctStatusCode", namespaces=namespace).text
                contact_no = root.find(".//ns:AcctInq_CustomData/ns:PreMobile_No", namespaces=namespace).text
                operation_mode = root.find(".//ns:AcctInq_CustomData/ns:MODE_OF_OPER_CODE", namespaces=namespace).text

                dt = datetime.strptime(acc_opening_date, "%Y-%m-%dT%H:%M:%S.%f")
                acc_opening_date = dt.strftime("%d-%m-%Y")
                
                for acct_bal in root.findall(".//ns:AcctBal", namespace):
                    bal_type = acct_bal.find("ns:BalType", namespaces=namespace).text
                    amount = acct_bal.find("ns:BalAmt/ns:amountValue", namespaces=namespace).text
                    if bal_type == "AVAIL":
                        bal_amt = amount
                if operation_mode == "SELF":
                    account_holder = str(prefix) + " " + str(acc_holder)
                else:
                    account_holder = str(acc_holder)

                acc_dtl={
                    "status": status,
                    "schm_type": schm_type, 
                    "cust_id": cust_id,
                    "account_no": account_no, 
                    "acc_holder": account_holder, 
                    "acc_opening_date": acc_opening_date, 
                    "bal_amt": bal_amt,
                    "contact_no": contact_no, 
                    "operation_mode": operation_mode,
                    "account_status": account_status
                }
                return acc_dtl
            else:
                return {"msg":status}
    except pycurl.error as e:
        frappe.throw(f"An error occurred: {e}")
    finally:
        c.close()
    c.close

@frappe.whitelist()
def td_account_inq(account_no=None, uuid=None, posting_date=None):
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    # url = "https://was1-dc-srv.bdbl.bt:11300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    # Optionally set a timeout
    c.setopt(c.TIMEOUT, 500)
    # Set SSL version to use TLS (if required)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    # Set the write data buffer
    c.setopt(c.WRITEDATA, buffer)
    # Follow redirects if needed
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    payload = """<?xml version="1.0" encoding="UTF-8"?>
            <FIXML xsi:schemaLocation="http://www.finacle.com/fixml TDAcctInq.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Header>
            <RequestHeader>
            <MessageKey>
            <RequestUUID>9063f3f7-49c8-0c4b-2c99a75dce77</RequestUUID>
            <ServiceRequestId>TDAcctInq</ServiceRequestId>
            <ServiceRequestVersion>10.2</ServiceRequestVersion>
            <ChannelId>COR</ChannelId>
            <LanguageId></LanguageId>
            </MessageKey>
            <RequestMessageInfo>
            <BankId>01</BankId>
            <TimeZone></TimeZone>
            <EntityId></EntityId>
            <EntityType></EntityType>
            <ArmCorrelationId></ArmCorrelationId>
            <MessageDateTime>2025-07-15T12:08:34.122</MessageDateTime>
            </RequestMessageInfo>
            <Security>
            <Token>
            <PasswordToken>
            <UserId></UserId>
            <Password></Password>
            </PasswordToken>
            </Token>
            <FICertToken></FICertToken>
            <RealUserLoginSessionId></RealUserLoginSessionId>
            <RealUser></RealUser>
            <RealUserPwd></RealUserPwd>
            <SSOTransferToken></SSOTransferToken>
            </Security>
            </RequestHeader>
            </Header>
            <Body>
            <TDAcctInqRequest>
            <TDAcctInqRq>
            <TDAcctId>
            <AcctId>{account_no}</AcctId>
            </TDAcctId>
            </TDAcctInqRq>
            </TDAcctInqRequest>
            </Body>
            </FIXML>""".format(account_no=account_no)

    headers = {
    'Content-Type': 'application/'
    'xml'
    }

    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    # Set the POST fields (SOAP body)
    c.setopt(c.POSTFIELDS, payload)
    # Set the write data buffer
    c.setopt(c.WRITEDATA, buffer)
    # Perform the request
    c.perform()
    # Get HTTP response code
    http_code = c.getinfo(c.RESPONSE_CODE)
    # Get the response body
    body = buffer.getvalue()
    result = str(body.decode('utf-8'))
    root = ET.fromstring(result)
    namespace = {'ns': 'http://www.finacle.com/fixml'}
    try:
        account_no = root.find('.//ns:AcctId', namespaces=namespace).text
        acc_holder = root.find(".//ns:CustId/ns:PersonName/ns:Name", namespaces=namespace).text
        acc_open_date = root.find('.//ns:AcctOpnDt', namespaces=namespace).text
        interest_rate = root.find('.//ns:NetIntRate/ns:value', namespaces=namespace).text
        installation = root.find('.//ns:CurrDeposit/ns:amountValue', namespaces=namespace).text
        current_balance = root.find('.//ns:AcctBalAmt/ns:amountValue', namespaces=namespace).text
        maturity_amount = root.find('.//ns:MaturityAmt/ns:amountValue', namespaces=namespace).text
        deposit_term = root.find('.//ns:DepositTerm/ns:Months', namespaces=namespace).text
        maturity_date = root.find('.//ns:MaturityDt', namespaces=namespace).text
        account_status = root.find('.//ns:BankAcctStatusCode', namespaces=namespace).text

        dt = datetime.strptime(acc_open_date, "%Y-%m-%dT%H:%M:%S.%f")
        acc_open_date = dt.strftime("%d-%m-%Y")
 
        
        dt = datetime.strptime(maturity_date, "%Y-%m-%dT%H:%M:%S.%f")
        maturity_date = dt.strftime("%d-%m-%Y")
        
        acc_dtl = {
            "account_no": account_no,
            "acc_holder": acc_holder,
            "acc_open_date": acc_open_date,
            "current_balance": current_balance,
            "interest_rate": interest_rate,
            "installation": installation,
            "maturity_amount": maturity_amount,
            "deposit_term": str(deposit_term) + " " + str("Months"),
            "maturity_date": maturity_date,
        }
        return acc_dtl
    except:
        return {"msg":"No Account Found"}
    c.close

def prepare_multi():
    data = {'message': [{'account': '100234567', 'amount': 484360.0, 'debit_credit': 'D', 'remark': 'IB260213/b'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}, {'account': '35345347856', 'amount': 60000.0, 'debit_credit': 'C', 'remark': 'IB260213/hofdhfd'}, {'account': '5334543456', 'amount': 545.0, 'debit_credit': 'C', 'remark': 'IB260213/dfgh'}]}
    for a in data['message']:
        print(a['account'], a['amount'])


@frappe.whitelist()
def multi_fund_transfer(data):
    posting_date=get_datetime()
    pd = str(posting_date).split(" ")[0]+"T"+str(posting_date).split(" ")[1]
    import random
    uuid = random.randint(100_000_000, 999_999_999)
    xml_data = ""
    sl=1
    records = data['message'] if isinstance(data, dict) else data
    for a in records:
        xml_data += """
                    <PartTrnRec>
                        <AcctId>
                            <AcctId>{account}</AcctId>
                        </AcctId>
                        <CreditDebitFlg>{debit_credit}</CreditDebitFlg>
                        <TrnAmt>
                            <amountValue>{amount}</amountValue>
                            <currencyCode>BTN</currencyCode>
                        </TrnAmt>
                        <TrnParticulars>{remark}</TrnParticulars>
                        <PartTrnRmks>{remark}</PartTrnRmks>
                        <ValueDt>{pd}</ValueDt>
                        <SerialNum>{sl}</SerialNum>
                    </PartTrnRec>
                """.format(account=a['account'],
                debit_credit=a['debit_credit'],
                amount=a['amount'],
                remark=a['remark'],
                pd=pd,
                sl=sl
            )
        sl += 1

    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://uat-dc-srv.bdbl.bt:22000/FISERVLET/fihttp"
    # url = "https://was1-dc-srv.bdbl.bt:11300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    c.setopt(c.TIMEOUT, 500)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    payload = """<?xml version="1.0" encoding="UTF-8"?>
                    <FIXML xsi:schemaLocation="http://www.finacle.com/fixml XferTrnAdd.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                        <Header>
                        <RequestHeader>
                        <MessageKey>
                        <RequestUUID>{uuid}</RequestUUID>
                        <ServiceRequestId>XferTrnAdd</ServiceRequestId>
                        <ServiceRequestVersion>10.2</ServiceRequestVersion>
                        <ChannelId>COR</ChannelId>
                        <LanguageId/>
                        </MessageKey>
                        <RequestMessageInfo>
                        <BankId>01</BankId>
                        <TimeZone/>
                        <EntityId/>
                        <EntityType/>
                        <ArmCorrelationId/>
                        <MessageDateTime>{pd}</MessageDateTime>
                        </RequestMessageInfo>
                        <Security>
                        <Token>
                        <PasswordToken>
                        <UserId/>
                        <Password/>
                        </PasswordToken>
                        </Token>
                        <FICertToken/>
                        <RealUserLoginSessionId/>
                        <RealUser/>
                        <RealUserPwd/>
                        <SSOTransferToken/>
                        </Security>
                        </RequestHeader>
                        </Header>
                        <Body>
                        <XferTrnAddRequest>
                        <XferTrnAddRq>
                        <XferTrnHdr>
                        <TrnType>T</TrnType>
                        <TrnSubType>CI</TrnSubType>
                        </XferTrnHdr>
                        <XferTrnDetail>
                        {xml_data}
                        </XferTrnDetail>
                        </XferTrnAddRq>
                    </XferTrnAddRequest>
                    </Body>
                </FIXML>
    """.format(uuid=uuid, xml_data=xml_data, pd=pd)

    headers = {
    'Content-Type': 'application/'
    'xml'
    }
    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    c.setopt(c.POSTFIELDS, payload)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    http_code = c.getinfo(c.RESPONSE_CODE)
    body = buffer.getvalue()
    result = str(body.decode('utf-8'))
    root = ET.fromstring(result)
    ns = {"fixml": "http://www.finacle.com/fixml"}
    status_elem = root.find(".//fixml:HostTransaction/fixml:Status", ns)
    status = status_elem.text if status_elem is not None else None

    trn_dt_elem = root.find(".//fixml:XferTrnAddResponse/fixml:XferTrnAddRs/fixml:TrnIdentifier/fixml:TrnDt", ns)
    trans_datetime = trn_dt_elem.text if trn_dt_elem is not None else None

    c.close
    return {
        "status": status,
        "trans_datetime": trans_datetime
    }

@frappe.whitelist()
def fund_transfer(from_account=None, to_account=None, amount=None, remark=None):
    posting_date=get_datetime()
    print(posting_date)
    pd = str(posting_date).split(" ")[0]+"T"+str(posting_date).split(" ")[1]
    import random
    uuid = random.randint(100_000_000, 999_999_999)
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    # url = "https://uat-dc-srv.bdbl.bt:22000/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    c.setopt(c.TIMEOUT, 500)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    pd = str(today())+"T00:00:00.000"
    payload = """<FIXML xsi:schemaLocation="http://www.finacle.com/fixml doFundsTransfer.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <RequestHeader>
            <MessageKey>
                <RequestUUID>{uuid}</RequestUUID>
                <ServiceRequestId>doFundsTransfer</ServiceRequestId>
                <ServiceRequestVersion>10.2</ServiceRequestVersion>
                <ChannelId>CRM</ChannelId>
            </MessageKey>
            <RequestMessageInfo>
                <BankId />
                <TimeZone />
                <EntityId />
                <EntityType />
                <ArmCorrelationId />
                <MessageDateTime>{pd}</MessageDateTime>
            </RequestMessageInfo>
            <Security>
                <Token>
                    <PasswordToken>
                        <UserId />
                        <Password />
                    </PasswordToken>
                </Token>
                <FICertToken />
                <RealUserLoginSessionId />
                <RealUser />
                <RealUserPwd />
                <SSOTransferToken />
            </Security>
        </RequestHeader>
    </Header>
    <Body>
        <doFundsTransferRequest>
            <ProcessFTInputVO>
                <frAcid>{from_account}</frAcid>
                <frBrchId>0010</frBrchId>
                <toAcid>{to_account}</toAcid>
                <toBrchId>0010</toBrchId>
                <txnAmt>
                    <amountValue>{amount}</amountValue>
                    <currencyCode>BTN</currencyCode>
                </txnAmt>
                <txnCrn>BTN</txnCrn>
                <valuedate>{pd}</valuedate>
                <tranRmks>{remark}</tranRmks>
            </ProcessFTInputVO>
        </doFundsTransferRequest>
    </Body>
</FIXML>""".format(uuid=uuid, pd=pd, from_account=from_account, to_account=to_account, amount=amount, remark=remark)

    headers = {
    'Content-Type': 'application/'
    'xml'
    }
    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    c.setopt(c.POSTFIELDS, payload)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    http_code = c.getinfo(c.RESPONSE_CODE)
    body = buffer.getvalue()
    result = str(body.decode('utf-8'))
    root = ET.fromstring(result)
    ns = {"fixml": "http://www.finacle.com/fixml"}
    status = root.find(".//fixml:HostTransaction/fixml:Status", ns).text
    trans_datetime = root.find(".//fixml:ResponseMessageInfo/fixml:MessageDateTime", ns).text
    c.close
    return {
        "status": status,
        "trans_datetime": trans_datetime
    }

@frappe.whitelist()
def loan_payment(loan_account=None, payment_account=None, amount=None, remark=None):
    posting_date=get_datetime()
    import random
    uuid = random.randint(100_000_000, 999_999_999)
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://was1-dc-srv.bdbl.bt:11300/FISERVLET/fihttp" #New Pro Server
    # url = "https://uat-dc-srv.bdbl.bt:22000/FISERVLET/fihttp" #New UAT Server
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    c.setopt(c.TIMEOUT, 500)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    pd = str(today())+"T00:00:00.000"
    payload = """<FIXML xsi:schemaLocation="http://www.finacle.com/fixml executeFinacleScript.xsd"
                    xmlns="http://www.finacle.com/fixml"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <Header>
                        <RequestHeader>
                            <MessageKey>
                                <RequestUUID>{uuid}</RequestUUID>
                                <ServiceRequestId>executeFinacleScript</ServiceRequestId>
                                <ServiceRequestVersion>10.2</ServiceRequestVersion>
                                <ChannelId>COR</ChannelId>
                                <LanguageId></LanguageId>
                            </MessageKey>
                            <RequestMessageInfo>
                                <BankId>01</BankId>
                                <TimeZone></TimeZone>
                                <EntityId></EntityId>
                                <EntityType></EntityType>
                                <ArmCorrelationId></ArmCorrelationId>
                                <MessageDateTime>{pd}</MessageDateTime>
                            </RequestMessageInfo>
                            <Security>
                                <Token>
                                    <PasswordToken>
                                        <UserId></UserId>
                                        <Password></Password>
                                    </PasswordToken>
                                </Token>
                                <FICertToken></FICertToken>
                                <RealUserLoginSessionId></RealUserLoginSessionId>
                                <RealUser></RealUser>
                                <RealUserPwd></RealUserPwd>
                                <SSOTransferToken></SSOTransferToken>
                            </Security>
                        </RequestHeader>
                    </Header>
                    <Body>
                        <executeFinacleScriptRequest>
                            <ExecuteFinacleScriptInputVO>
                                <requestId>LoanPaymentAPI.scr</requestId>
                            </ExecuteFinacleScriptInputVO>
                            <executeFinacleScript_CustomData>
                                <ofcAcctNum>{payment_account}</ofcAcctNum>
                                <loanAcctNum>{loan_account}</loanAcctNum>
                                <tranAmt>{amount}</tranAmt>
                            </executeFinacleScript_CustomData>
                        </executeFinacleScriptRequest>
                    </Body>
                </FIXML>
    """.format(uuid=uuid, pd=pd, loan_account=loan_account, payment_account=payment_account, amount=amount)
    headers = {
    'Content-Type': 'application/'
    'xml'
    }
    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    c.setopt(c.POSTFIELDS, payload)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    http_code = c.getinfo(c.RESPONSE_CODE)
    body = buffer.getvalue()
    result = str(body.decode('utf-8'))
    root = ET.fromstring(result)
    ns = {"fixml": "http://www.finacle.com/fixml"}
    status = root.find(".//fixml:_trandetails/fixml:Status", ns).text
    c.close
    return status

@frappe.whitelist()
def getLastTransactions(account=None, tran_nos=None):
    posting_date=get_datetime()
    import random
    uuid = random.randint(100_000_000, 999_999_999)
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    # url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    c.setopt(c.TIMEOUT, 500)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    pd = str(today())+"T00:00:00.000"
    payload = """<?xml version="1.0" encoding="UTF-8"?>
                <FIXML xsi:schemaLocation="http://www.finacle.com/fixml getLastNTransactions.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <Header><RequestHeader>
                <MessageKey>
                    <RequestUUID>{uuid}</RequestUUID>
                    <ServiceRequestId>getLastNTransactions</ServiceRequestId>
                    <ServiceRequestVersion>10.2</ServiceRequestVersion>
                    <ChannelId>CRM</ChannelId>
                </MessageKey>
                <RequestMessageInfo><BankId /><TimeZone /><EntityId /><EntityType /><ArmCorrelationId />
                <MessageDateTime>{pd}</MessageDateTime>
                </RequestMessageInfo><Security><Token><PasswordToken><UserId /><Password /></PasswordToken></Token><FICertToken />
                <RealUserLoginSessionId /><RealUser /><RealUserPwd /><SSOTransferToken /></Security>
                </RequestHeader>
                </Header>
                <Body>
                    <getLastNTransactionsRequest>
                    <accountTransactionList>
                        <accountListElement>
                        <acid>{account}</acid>
                        <branchId>0010</branchId>
                        </accountListElement>
                        <lastNTransactions>{tran_nos}</lastNTransactions>
                    </accountTransactionList>
                    <getLastNTransactionRequest_CustomData />
                    </getLastNTransactionsRequest>
                </Body>
                </FIXML>""".format(uuid=uuid,pd=pd,account=account,tran_nos=tran_nos)
    headers = {
    'Content-Type': 'application/'
    'xml'
    }
    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    c.setopt(c.POSTFIELDS, payload)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    http_code = c.getinfo(c.RESPONSE_CODE)
    body = buffer.getvalue()
    result = str(body.decode('utf-8'))
    root = ET.fromstring(result)
    try:
        ns = {"fixml": "http://www.finacle.com/fixml"}
        available_balance = root.find(".//fixml:ledgerBalance/fixml:amountValue", ns).text
        transactions = []
        for txn in root.findall(".//fixml:transactionDetails", ns):
            pstdDate = txn.find("fixml:pstdDate", ns).text
            txnAmt = txn.find(".//fixml:txnAmt/fixml:amountValue", ns).text
            txnDesc = txn.find(".//fixml:txnDesc", ns).text.strip()
            txnType = txn.find(".//fixml:txnType", ns).text
            txnBalance = txn.find(".//fixml:txnBalance/fixml:amountValue", ns).text

            transactions.append({
                "txnAmt": txnAmt,
                "pstdDate": pstdDate,
                "txnDesc": txnDesc,
                "txnType": txnType,
                "txnBalance": txnBalance
            })

        result = {
            "availableBalance": available_balance,
            "transactionDetails": transactions
        }
        return result
    except:
        return {"msg":"No record Found"}

@frappe.whitelist()
def getFullStatement(account=None, from_date=None, to_date=None):
    posting_date=get_datetime()
    import random
    uuid = random.randint(100_000_000, 999_999_999)
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    # url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    c.setopt(c.TIMEOUT, 500)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    pd = str(today())+"T00:00:00.000"
    from_date = str(from_date)+"T00:00:00.000"
    to_date = str(to_date)+"T23:59:00.000"
    payload = """<FIXML
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns="http://www.finacle.com/fixml" xsi:schemaLocation="http://www.finacle.com/fixml getFullAccountStatementRequest.xsd">
                <Header>
                    <RequestHeader>
                        <MessageKey>
                            <RequestUUID>{uuid}</RequestUUID>
                            <ServiceRequestId>getFullAccountStatement</ServiceRequestId>
                            <ServiceRequestVersion>10.2</ServiceRequestVersion>
                            <ChannelId>CRM</ChannelId>
                        </MessageKey>
                        <RequestMessageInfo>
                            <BankId/>
                            <TimeZone/>
                            <EntityId/>
                            <EntityType/>
                            <ArmCorrelationId/>
                            <MessageDateTime>{pd}</MessageDateTime>
                        </RequestMessageInfo>
                        <Security>
                            <Token>
                                <PasswordToken>
                                    <UserId/>
                                    <Password/>
                                </PasswordToken>
                            </Token>
                            <FICertToken/>
                            <RealUserLoginSessionId/>
                            <RealUser/>
                            <RealUserPwd/>
                            <SSOTransferToken/>
                        </Security>
                    </RequestHeader>
                </Header>
                <Body>
                    <getFullAccountStatementRequest>
                        <AccountTransactionCriteria>
                            <acid>{account}</acid>
                            <beginChkNo/>
                            <branchId>0010</branchId>
                            <endChkNo/>
                            <fromDate>{from_date}</fromDate>
                            <maxAmt>
                                <amountValue/>
                                <currencyCode/>
                            </maxAmt>
                            <minAmt>
                                <amountValue/>
                                <currencyCode/>
                            </minAmt>
                            <numOfTxns/>
                            <sortIn/>
                            <txnType/>
                            <toDate>{to_date}</toDate>
                        </AccountTransactionCriteria>
                        <getFullAccountStatement_CustomData/>
                    </getFullAccountStatementRequest>
                </Body>
            </FIXML>""".format(uuid=uuid,pd=pd,account=account,from_date=from_date,to_date=to_date)
    headers = {
    'Content-Type': 'application/'
    'xml'
    }
    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    c.setopt(c.POSTFIELDS, payload)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    http_code = c.getinfo(c.RESPONSE_CODE)
    body = buffer.getvalue()
    result = str(body.decode('utf-8'))
    root = ET.fromstring(result)
    try:
        ns = {"fixml": "http://www.finacle.com/fixml"}
        available_balance = root.find(".//fixml:ledgerBalance/fixml:amountValue", ns).text
        transactions = []
        for txn in root.findall(".//fixml:transactionDetails", ns):
            pstdDate = txn.find("fixml:pstdDate", ns).text
            txnAmt = txn.find(".//fixml:txnAmt/fixml:amountValue", ns).text
            txnDesc = txn.find(".//fixml:txnDesc", ns).text.strip()
            txnType = txn.find(".//fixml:txnType", ns).text
            txnBalance = txn.find(".//fixml:txnBalance/fixml:amountValue", ns).text

            transactions.append({
                "txnAmt": txnAmt,
                "pstdDate": pstdDate,
                "txnDesc": txnDesc,
                "txnType": txnType,
                "txnBalance": txnBalance
            })

        result = {
            "availableBalance": available_balance,
            "transactionDetails": transactions
        }
        return result
    
    except:
        return {"msg":"No record Found"}



