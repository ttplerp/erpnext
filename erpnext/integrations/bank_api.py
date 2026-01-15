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
from erpnext.cbs_integration.doctype.cbs import show_progress
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context
from http.client import HTTPConnection  # py3
import http.client
from urllib.request import urlopen
import os
# import httpx
import logging
import traceback
import json

class BankAPI:
    pass

class SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        # Create a pool manager with the custom SSL context
        context = self.ssl_context or create_urllib3_context()

        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# class MyAdapter(HTTPAdapter):
#     def init_poolmanager(self, connections, maxsize, block=False):
#         self.poolmanager = PoolManager(num_pools=connections,
#                                        maxsize=maxsize,
#                                        block=block,
#                                        ssl_version=ssl.PROTOCOL_TLSv1)

def post_transaction(cbs_entry=None, posting_date = None, doctype=None, doc_name=None, publish_progress=False):
    show_progress(publish_progress, 55, 'Posting Entry {}...'.format(cbs_entry), 'CBS posting progress...')
    debit = credit = 0
    status_from_cbs = None
    status_list = []
    response_list = []
    header = generate_header(cbs_entry, doctype, doc_name, posting_date=str(posting_date))
    footer = generate_footer()
    payload, d, cr = generate_payload(cbs_entry, doctype, doc_name)
    #frappe.errprint(str(payload))
    #frappe.throw("here")
    # Create a custom SSL context
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    count = 1
    #-----Main CBS Posting Code Block Begins --------------------------------------------------------------------------
    # Initialize a pycurl object
    c = pycurl.Curl()
    c.setopt(c.URL, url)
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
    header = generate_header(cbs_entry, doctype, doc_name, posting_date=str(posting_date), count=count)
    footer = generate_footer()
    debit += d
    credit += cr
    api_body = str(header) + str(payload) + str(footer)
    frappe.errprint(api_body)
    headers = {
    'Content-Type': 'application/xml'
    }
    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    # Set the POST fields (SOAP body)
    c.setopt(c.POSTFIELDS, api_body)
    # Set the write data buffer
    c.setopt(c.WRITEDATA, buffer)
    # Perform the request
    try:
        c.perform()
        # Get HTTP response code
        http_code = c.getinfo(c.RESPONSE_CODE)
        # Get the response body
        body = buffer.getvalue()
        log = cbs_entry.append("logs", {})
        log.log_message = str(body.decode('utf-8'))
        log.total_debit = debit
        log.total_credit = credit
        # frappe.errprint(str(log.log_message))
        # frappe.throw('here')
        # Parse the XML string
        if log.log_message:
            root = ET.fromstring(log.log_message)
            # Define the namespace
            namespace = {'ns': 'http://www.finacle.com/fixml'}
            log.cbs_status = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
            cbs_entry.cbs_status = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
            if cbs_entry.cbs_status == "FAILURE":
                log.log_type = "Error"
            elif cbs_entry.cbs_status == "SUCCESS":
                log.cbs_transaction_id = root.find('.//ns:TrnIdentifier/ns:TrnId', namespaces=namespace).text
                status_from_cbs = "Success"
    except pycurl.error as e:
        # frappe.throw(traceback.format_exc())
        frappe.throw(f"An error occurred: {e}")
    finally:
        # Close the curl object
        c.close()
    c.close
    if status_from_cbs == "Success":
         message = "Posting Complete...."
    else:
        message = "Posting Failed...."
    show_progress(publish_progress, 99, message, 'CBS posting progress...')
    return status_from_cbs  

def generate_payload(cbs_entry=None, doctype=None, doc_name=None):
    # payload_list = []
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    # header = (str(doc.header).format(uuid=cbs_entry.name, bankid="01", msgdatetime=pd))
    # footer = str(doc.footer)
    end_point=doc.api_link
    serialnumber = 1
    d = c = 0
    payload = ""
    if not doctype and not doc_name:
        if cbs_entry:
            for a in frappe.db.sql("""
                                    select * from `tabCBS Entry Upload` where cbs_entry = '{}' 
                                """.format(cbs_entry.name), as_dict=True):
                creditdebit = "D" if flt(a.debit) > 0 else "C"
                gl_entry = ""
                amount = flt(a.debit,2) if flt(a.debit) > 0 else flt(a.credit,2)
                if amount < 0:
                    amount = -1 * amount
                acc_doc = frappe.get_doc("Account", a.account)
                d += flt(a.debit,2)
                c += flt(a.credit,2)                        
                pd = str(today())+"T00:00:00.000"
                payload += doc.body.format(acctid=a.account_number,creditdebit=creditdebit,\
                    amount=amount,trnparticular=str(cbs_entry.entry_title)[:30],trnrmks="",\
                    valuedate=pd,serialnumber=serialnumber)
                serialnumber += 1
        else:
            for a in frappe.db.sql("""
                                    select * from `tabCBS Entry Upload`
                            """.format(), as_dict=True):
                    creditdebit = "D" if flt(a.debit) > 0 else "C"
                    amount = flt(a.debit,2) if flt(a.debit) > 0 else flt(a.credit,2)
                    d += flt(a.debit,2)
                    c += flt(a.credit,2)
                    pd = str(a.creation)[:-3].split(" ")[0]+"T"+str(a.creation)[:-3].split(" ")[1]
                    payload += doc.body.format(acctid=a.account_number,creditdebit=creditdebit,\
                        amount=amount,trnparticular=a.remarks,trnrmks=a.remarks,\
                        valuedate=pd,serialnumber=serialnumber)
                    serialnumber += 1
    else:
        for a in frappe.db.sql("""
                            select * from `tabCBS Entry Upload`
                            where voucher_type="{0}"
                            and voucher_no="{1}"
                    """.format(doctype, doc_name), as_dict=True):
            creditdebit = "D" if flt(a.debit) > 0 else "C"
            amount = flt(a.debit,2) if flt(a.debit) > 0 else flt(a.credit,2)
            d += flt(a.debit,2)
            c += flt(a.credit,2)
            acc_doc = frappe.get_doc("Account", a.account)
            pd = str(a.creation)[:-3].split(" ")[0]+"T"+str(a.creation)[:-3].split(" ")[1]
            payload += doc.body.format(acctid=acc_doc.account_number,creditdebit=creditdebit,\
            amount=amount,trnparticular=a.account_number,trnrmks=a.account_number,\
            valuedate=pd,serialnumber=serialnumber)
            serialnumber += 1
    return payload, d, c

@frappe.whitelist()
def bill_payment():
    import pycurl
    buffer = BytesIO()
    url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    # Initialize a pycurl object
    print(ssl.OPENSSL_VERSION)
    print(pycurl.version)
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
    posting_date ="2025-06-05 00:00:00"
    pd = str(posting_date).split(" ")[0]+"T"+str(posting_date).split(" ")[1]+".000"
    # Define the XML body as a string
    rfid = "1232423422"
    amount = "2200.00"
    frm_acid = "101028916201"
    frm_branch_id = "0230"

    payload = """<FIXML xsi:schemaLocation="http://www.finacle.com/fixml doFundsTransfer.xsd"
        xmlns="http://www.finacle.com/fixml"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <Header>
            <RequestHeader>
                <MessageKey>
                    <RequestUUID>{rfid}</RequestUUID>
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
                    <frAcid>{frm_acid}</frAcid>
                    <frBrchId>{frm_branch_id}</frBrchId>
                    <toAcid>0000220010014</toAcid>
                    <toBrchId>0010</toBrchId>
                    <txnAmt>
                        <amountValue>{amount}</amountValue>
                        <currencyCode>BTN</currencyCode>
                    </txnAmt>
                    <txnCrn>BTN</txnCrn>
                    <valuedate>2024-10-19T18:47:56.749</valuedate>
                    <tranRmks>04293184756686/BT Leaseline/</tranRmks>
                </ProcessFTInputVO>
            </doFundsTransferRequest>
        </Body>
    </FIXML>""".format(rfid = rfid, frm_acid = frm_acid, frm_branch_id = frm_branch_id, amount = amount, pd=pd)
    
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
        print(result)
        if result:
            root = ET.fromstring(result)
            # Define the namespace
            namespace = {'ns': 'http://www.finacle.com/fixml'}
            response = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
        return response
    except pycurl.error as e:
        # frappe.throw(traceback.format_exc())
        frappe.throw(f"An error occurred: {e}")
    finally:
        # Close the curl object
        c.close()
    c.close

def generate_footer(doctype=None, doc_name=None):
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    return str(doc.footer)

def generate_header(cbs_entry=None, doctype=None, doc_name=None, posting_date=None, count=1):
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    pd = str(posting_date).split(" ")[0]+"T"+str(posting_date).split(" ")[1]+".000"
    return(str(doc.header).format(uuid=cbs_entry.name, bankid="01", msgdatetime=pd))

def gst_api_header():
    pd = str(today())+"T00:00:00.000"
    import random
    uuid = random.randint(100_000_000, 999_999_999)
    return """<?xml version="1.0" encoding="UTF-8"?>
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
        <XferTrnDetail> """.format(uuid=uuid, pd=pd)

def gst_api_footer():
    return """</XferTrnDetail>
        </XferTrnAddRq>
        </XferTrnAddRequest>
        </Body>
        </FIXML>"""

def gst_entry_adjustment(docname=None):
    body=""
    if docname:
        body_flag = 0
        doc = frappe.get_doc("GST Invoice", docname)
        pd = str(today())+"T00:00:00.000"
        for a in doc.get("item"):
            service_acc = str(doc.branch_code)+str(a.service_gl_account)
            gst_acc = str(doc.branch_code)+str(a.gst_gl_account)

            sl = 0
            if a.require_adjustment == 1:
                body_flag = 1
                sl += 1
                body += """
                    <PartTrnRec>
                    <AcctId>
                    <AcctId>{service_acc}</AcctId>
                    </AcctId>
                    <CreditDebitFlg>D</CreditDebitFlg>
                    <TrnAmt>
                    <amountValue>{amt}</amountValue>
                    <currencyCode>BTN</currencyCode>
                    </TrnAmt>
                    <TrnParticulars>{particular}</TrnParticulars>
                    <PartTrnRmks>{rmks}</PartTrnRmks>
                    <ValueDt>{pd}</ValueDt>
                    <SerialNum>{sl}</SerialNum>
                    </PartTrnRec>

                    <PartTrnRec>
                    <AcctId>
                    <AcctId>{gst_acc}</AcctId>
                    </AcctId>
                    <CreditDebitFlg>C</CreditDebitFlg>
                    <TrnAmt>
                    <amountValue>{amt}</amountValue>
                    <currencyCode>BTN</currencyCode>
                    </TrnAmt>
                    <TrnParticulars>{particular}</TrnParticulars>
                    <PartTrnRmks>{rmks}</PartTrnRmks>
                    <ValueDt>{pd}</ValueDt>
                    <SerialNum>{sl}</SerialNum>
                    </PartTrnRec>
                """.format(service_acc=service_acc,gst_acc=gst_acc,amt=a.gst,particular=a.service_type,rmks=str(docname) + ' ' + str(a.service_type),pd=pd,sl=sl)
    if body_flag == 0:
        return "Not Required", ""

    payload = str(gst_api_header()) + str(body) + str(gst_api_footer())
    import pycurl
    buffer = BytesIO()
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
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

    headers = {
    'Content-Type': 'application/'
    'xml'
    }

    c.setopt(c.HTTPHEADER, [
        'Content-Type: application/xml; charset=utf-8'
    ])
    c.setopt(c.POSTFIELDS, payload)
    c.setopt(c.WRITEDATA, buffer)
    # Perform the request
    try:
        c.perform()
        # Get HTTP response code
        http_code = c.getinfo(c.RESPONSE_CODE)
        # Get the response body
        body = buffer.getvalue()
        result = str(body.decode('utf-8'))
        response = msg = ""
        if result:
            root = ET.fromstring(result)
            # Define the namespace
            namespace = {'ns': 'http://www.finacle.com/fixml'}
            response = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
            if response == "SUCCESS":
                msg = root.find('.//ns:TrnIdentifier/ns:TrnId', namespaces=namespace).text
            elif response == "FAILURE":
                msg = root.find('.//ns:ErrorDetail/ns:ErrorDesc', namespaces=namespace).text
        return response, msg
    except pycurl.error as e:
        frappe.throw(f"An error occurred: {e}")
    finally:
        c.close()

@frappe.whitelist()
def activate_dormant_account(uuid=None, posting_date=None, account_no=None):
    import pycurl
    buffer = BytesIO()
    # url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    # Initialize a pycurl object
    print(ssl.OPENSSL_VERSION)
    print(pycurl.version)
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
    pd = str(posting_date).split(" ")[0]+"T"+str(posting_date).split(" ")[1]+".000"
    payload = """<?xml version="1.0" encoding="UTF-8"?>
<FIXML xsi:schemaLocation="http://www.finacle.com/fixml SBAcctMod.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Header>
        <RequestHeader>
            <MessageKey>
                <RequestUUID>{0}</RequestUUID>
                <ServiceRequestId>SBAcctMod</ServiceRequestId>
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
                <MessageDateTime>{1}</MessageDateTime>
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
        <SBAcctModRequest>
            <SBAcctModRq>
                <DespatchMode>N</DespatchMode>
                <SBAcctId>
                    <AcctId>{2}</AcctId>
                </SBAcctId>
                <SBAcctMod_CustomData>
                    <acctStatus>A</acctStatus>
                </SBAcctMod_CustomData>              
           </SBAcctModRq>
        </SBAcctModRequest>
    </Body>
</FIXML>""".format(uuid, pd, account_no)

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
        if result:
            root = ET.fromstring(result)
            # Define the namespace
            namespace = {'ns': 'http://www.finacle.com/fixml'}
            response = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
            if response == "FAILURE":
                error_desc = root.find(".//ns:ErrorDesc", namespaces=namespace).text +" "+ root.find(".//ns:ErrorSource", namespaces=namespace).text
                return response, error_desc
            else:
                message = "Successful"
                return response, message
    except pycurl.error as e:
        # frappe.throw(traceback.format_exc())
        frappe.throw(f"An error occurred: {e}")
    finally:
        # Close the curl object
        c.close()
    c.close

@frappe.whitelist()
def request_freeze_account(account_no=None):
    print(account_no)
    import pycurl
    buffer = BytesIO()
    url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    # Initialize a pycurl object
    print(ssl.OPENSSL_VERSION)
    print(pycurl.version)
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
    payload = """
        <?xml version="1.0" encoding="UTF-8"?>
            <FIXML xsi:schemaLocation="http://www.finacle.com/fixml executeFinacleScript.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><Header>
            <RequestHeader>
            <MessageKey>
            <RequestUUID>Req45453899999</RequestUUID>
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
            <requestId>FreezeUpdate.scr</requestId>
            </ExecuteFinacleScriptInputVO>
            <executeFinacleScript_CustomData>
            <AcctId>{0}</AcctId>
            <FreezeCode>T</FreezeCode>
            </executeFinacleScript_CustomData>
            </executeFinacleScriptRequest>
            </Body>
            </FIXML>
    """.format(account_no)

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
        if result:
            root = ET.fromstring(result)
            # Define the namespace
            namespace = {'ns': 'http://www.finacle.com/fixml'}
            response = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
            print(response)
        return response
    except pycurl.error as e:
        frappe.throw(f"An error occurred: {e}")
    finally:
        c.close()
    c.close

@frappe.whitelist()
def print_result():
    result="<FIXML xsi:schemaLocation=\"http://www.finacle.com/fixml SBAcctMod.xsd\" xmlns=\"http://www.finacle.com/fixml\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">\n<Header>\n<ResponseHeader>\n<RequestMessageKey>\n<RequestUUID>12341234</RequestUUID>\n<ServiceRequestId>SBAcctMod</ServiceRequestId>\n<ServiceRequestVersion>10.2</ServiceRequestVersion>\n<ChannelId>COR</ChannelId>\n</RequestMessageKey>\n<ResponseMessageInfo>\n<BankId>01</BankId>\n<TimeZone></TimeZone>\n<MessageDateTime>2025-04-23T10:42:53.503</MessageDateTime>\n</ResponseMessageInfo><UBUSTransaction>\n<Id/>\n<Status/>\n</UBUSTransaction>\n<HostTransaction>\n<Id/>\n<Status>SUCCESS</Status>\n</HostTransaction>\n<HostParentTransaction>\n<Id/>\n<Status/>\n</HostParentTransaction>\n<CustomInfo/>\n</ResponseHeader>\n</Header>\n<Body>\n<SBAcctModResponse>\n<SBAcctModRs>\n<SBAcctId>\n<AcctId>001715160147</AcctId>\n<AcctType>\n<SchmCode></SchmCode>\n<SchmType></SchmType>\n</AcctType>\n<AcctCurr></AcctCurr>\n<BankInfo>\n<BankId></BankId>\n<Name></Name>\n<BranchId></BranchId>\n<BranchName></BranchName>\n<PostAddr>\n<Addr1></Addr1>\n<Addr2></Addr2>\n<Addr3></Addr3>\n<City></City>\n<StateProv></StateProv>\n<PostalCode></PostalCode>\n<Country></Country>\n<AddrType></AddrType>\n</PostAddr>\n</BankInfo>\n</SBAcctId>\n</SBAcctModRs><SBAcctMod_CustomData/>\n</SBAcctModResponse></Body></FIXML>\n"
    if result:
        root = ET.fromstring(result)
        # Define the namespace
        namespace = {'ns': 'http://www.finacle.com/fixml'}
        cbs_status = root.find('.//ns:HostTransaction/ns:Status', namespaces=namespace).text
        if cbs_status == "SUCCESS":
            print("SUCCESS")
        else:
            print("FAILED")

@frappe.whitelist()
def loan_account_inq(account_no=None):
    buffer = BytesIO()
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
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
        sanction_date = root.find('.//ns:sanction_date', namespaces=namespace).text
        acc_status = root.find('.//ns:ACCT_STATUS', namespaces=namespace).text
        interest_rate = root.find('.//ns:interest_rate', namespaces=namespace).text
        principal_os = root.find('.//ns:principal_OS', namespaces=namespace).text
        overdue_amt = root.find('.//ns:Overdue_Amt', namespaces=namespace).text
        outstanding_amt = root.find('.//ns:Total_Outstanding', namespaces=namespace).text
        next_payment_date = root.find('.//ns:NEXT_DMD_DATE', namespaces=namespace).text 
        emi_amt = root.find('.//ns:installment_Amount', namespaces=namespace).text
        
        dt = datetime.strptime(sanction_date, "%Y-%m-%dT%H:%M:%S.%f")
        sanction_date = dt.strftime("%d-%m-%Y")

        dt = datetime.strptime(next_payment_date, "%Y-%m-%dT%H:%M:%S.%f")
        next_payment_date = dt.strftime("%d-%m-%Y")
         
        acc_dtl = {
            "account_no": account_no,
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
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
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
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
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
