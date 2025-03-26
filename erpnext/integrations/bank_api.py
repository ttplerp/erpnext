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
    #-----CBS Posting Code Block End -----------------------------------------------------------------------------------

    #-----Commented below code block incase CBS TLS and OPENSSL Version gets upgraded in future--------------------
    # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    # context.options |= ssl.OP_NO_TLSv1_1  # Disable TLSv1 and TLSv1.1
    # context.options |= ssl.OP_NO_TLSv1_2  # Disable TLSv1 and TLSv1.1
    # context.set_ciphers = ('AES128-SHA256')
    # session = requests.Session()
    # session.mount('http://', SSLAdapter(ssl_context=context))
    # try:
    #     response = session.post(
    #         url,
    #         headers={"Content-Type": "application/xml"},
    #         data=api_body,
    #         verify='/etc/ssl/certs/server-cert.pem',
    #         # proxies=proxies# Mimics rejectUnauthorized: false,
    #     )

    #     response.raise_for_status()  # Raise an error for bad responses
    #     # Parse the XML response
    #     # parsed_response = xmltodict.parse(response.content)
    #     frappe.throw(str(response.content))
    # except requests.exceptions.RequestException as e:
    #     frappe.throw(f"Error: {e}")
    #     frappe.throw({"error": str(e)}), 500
    # response = requests.request("POST", url, headers=headers, data=api_body)
    #--------------------------------------------------------------------------------------------------------=
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
            # if len(frappe.db.sql("""
            #                         select * from `tabCBS Entry Upload` where cbs_entry = '{}' 
            #                 """.format(cbs_entry.name), as_dict=True)) > 200:
            for a in frappe.db.sql("""
                                    select * from `tabCBS Entry Upload` where cbs_entry = '{}' 
                            """.format(cbs_entry.name), as_dict=True):
                creditdebit = "D" if flt(a.debit) > 0 else "C"

                # gl_entry = frappe.get_doc("GL Entry", a.gl_entry)
                gl_entry = ""
                amount = flt(a.debit,2) if flt(a.debit) > 0 else flt(a.credit,2)
                if amount < 0:
                    amount = -1 * amount
                acc_doc = frappe.get_doc("Account", a.account)
                d += flt(a.debit,2)
                c += flt(a.credit,2)

  
                        
                pd = str(today())+"T00:00:00.000"
                #pd = "2024-10-31T00:00:00.000"
                # if gl_entry.partylist_json:
                #     # Parse the JSON string into a Python dictionary
                #     party_data = json.loads(gl_entry.partylist_json)
                #     for ptype in party_data:
                #         for party_detail in party_data[ptype]:
                #             payload += doc.body.format(acctid=party_detail['account_number'],creditdebit=creditdebit,\
                #                 amount=party_detail['amount'],trnparticular=gl_entry.remarks+" "+party_detail["remarks"],trnrmks=gl_entry.remarks+" "+party_detail["remarks"],\
                #                 valuedate=pd,serialnumber=serialnumber)
                #             serialnumber += 1
                # else:
                payload += doc.body.format(acctid=a.account_number,creditdebit=creditdebit,\
                    amount=amount,trnparticular=str(cbs_entry.entry_title)[:30],trnrmks="",\
                    valuedate=pd,serialnumber=serialnumber)
                # if serialnumber < 201:
                serialnumber += 1
                # if serialnumber == 201:
                #     payload_list.append(str(payload))
                #     serialnumber = 1
        # else:
        #     for a in frappe.db.sql("""
        #                             select * from `tabCBS Entry Upload` where cbs_entry = '{}' 
        #                     """.format(cbs_entry.name), as_dict=True):
        #             creditdebit = "D" if flt(a.debit) > 0 else "C"
        #             gl_entry = frappe.get_doc("GL Entry", a.gl_entry)
        #             amount = flt(a.debit,2) if flt(a.debit) > 0 else flt(a.credit,2)
        #             if amount < 0:
        #                 amount = -1 * amount
        #             acc_doc = frappe.get_doc("Account", a.account)
        #             d += flt(a.debit,2)
        #             c += flt(a.credit,2)

                                
                            
        #             pd = str(gl_entry.posting_date)+"T00:00:00.000"
        #             # if gl_entry.partylist_json:
        #             #     # Parse the JSON string into a Python dictionary
        #             #     party_data = json.loads(gl_entry.partylist_json)
        #             #     for ptype in party_data:
        #             #         for party_detail in party_data[ptype]:
        #             #             payload += doc.body.format(acctid=party_detail['account_number'],creditdebit=creditdebit,\
        #             #                 amount=party_detail['amount'],trnparticular=gl_entry.remarks+" "+party_detail["remarks"],trnrmks=gl_entry.remarks+" "+party_detail["remarks"],\
        #             #                 valuedate=pd,serialnumber=serialnumber)
        #             #             serialnumber += 1
        #             # else:
        #             payload += doc.body.format(acctid=a.account_number,creditdebit=creditdebit,\
        #                 amount=amount,trnparticular=a.account_number,trnrmks=a.account_number,\
        #                 valuedate=pd,serialnumber=serialnumber)
        #             serialnumber += 1
        else:
            for a in frappe.db.sql("""
                                    select * from `tabCBS Entry Upload`
                            """.format(), as_dict=True):
                    creditdebit = "D" if flt(a.debit) > 0 else "C"
                    amount = flt(a.debit,2) if flt(a.debit) > 0 else flt(a.credit,2)
                    d += flt(a.debit,2)
                    c += flt(a.credit,2)
                    # acc_doc = frappe.get_doc("Account", a.account)
                    # payload += """
                    #         <PartTrnRec>
                    #         <AcctId>
                    #         <AcctId>{acctid}</AcctId>
                    #         </AcctId>
                    #         <CreditDebitFlg>{creditdebit}</CreditDebitFlg>
                    #         <TrnAmt>
                    #         <amountValue>{amount}</amountValue>
                    #         <currencyCode>BTN</currencyCode>
                    #         </TrnAmt>
                    #         <TrnParticulars>{trnparticular}</TrnParticulars>
                    #         <PartTrnRmks>{trnrmks}</PartTrnRmks>
                    #         <ValueDt>{valuedate}</ValueDt>
                    #         <SerialNum>{serialnumber}</SerialNum>
                    #         </PartTrnRec>
                    #     """.format(acctid=acc_doc.account_number,creditdebit=creditdebit,\
                    #     amount=amount,trnparticular=a.account_number,trnrmks=a.account_number,\
                    #     valuedate=a.creation,serialnumber=serialnumber)
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
            # payload += """
            #         <PartTrnRec>
            #         <AcctId>
            #         <AcctId>{acctid}</AcctId>
            #         </AcctId>
            #         <CreditDebitFlg>{creditdebit}</CreditDebitFlg>
            #         <TrnAmt>
            #         <amountValue>{amount}</amountValue>
            #         <currencyCode>BTN</currencyCode>
            #         </TrnAmt>
            #         <TrnParticulars>{trnparticular}</TrnParticulars>
            #         <PartTrnRmks>{trnrmks}</PartTrnRmks>
            #         <ValueDt>{valuedate}</ValueDt>
            #         <SerialNum>{serialnumber}</SerialNum>
            #         </PartTrnRec>
            #     """.format(acctid=acc_doc.account_number,creditdebit=creditdebit,\
            #     amount=amount,trnparticular=a.account_number,trnrmks=a.account_number,\
            #     valuedate=a.creation,serialnumber=serialnumber)
            pd = str(a.creation)[:-3].split(" ")[0]+"T"+str(a.creation)[:-3].split(" ")[1]
            payload += doc.body.format(acctid=acc_doc.account_number,creditdebit=creditdebit,\
            amount=amount,trnparticular=a.account_number,trnrmks=a.account_number,\
            valuedate=pd,serialnumber=serialnumber)
            serialnumber += 1
    # for a in frappe.db.sql("""
    #                     select * from `tabGL Entry`
    #                     where voucher_type="{0}"
    #                     and voucher_no="{1}"
    #             """.format(doctype, doc_name), as_dict=True):
    #     creditdebit = "D" if a.debit > 0 else "C"
    #     amount = flt(a.debit,2) if a.debit >0 else flt(a.credit,2)
    #     acc_doc = frappe.get_doc("Account", a.account)
    #     payload += """
    #             <PartTrnRec>
    #             <AcctId>
    #             <AcctId>{acctid}</AcctId>
    #             </AcctId>
    #             <CreditDebitFlg>{creditdebit}</CreditDebitFlg>
    #             <TrnAmt>
    #             <amountValue>{amount}</amountValue>
    #             <currencyCode>BTN</currencyCode>
    #             </TrnAmt>
    #             <TrnParticulars>{trnparticular}</TrnParticulars>
    #             <PartTrnRmks>{trnrmks}</PartTrnRmks>
    #             <ValueDt>{valuedate}</ValueDt>
    #             <SerialNum>{serialnumber}</SerialNum>
    #             </PartTrnRec>
    #         """.format(acctid=acc_doc.account_number,creditdebit=creditdebit,\
    #         amount=amount,trnparticular=a.account_number,trnrmks=a.account_number,\
    #         valuedate=a.creation,serialnumber=serialnumber)
    #     serialnumber += 1
    return payload, d, c 

def generate_footer(doctype=None, doc_name=None):
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    # return """
    #         </XferTrnDetail>
    #         </XferTrnAddRq>
    #         </XferTrnAddRequest>
    #         </Body>
    #         </FIXML
    #     """
    return str(doc.footer)

def generate_header(cbs_entry=None, doctype=None, doc_name=None, posting_date=None, count=1):
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    # return """
    #         <FIXML xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.finacle.com/fixml XferTrnAdd.xsd">
    #         <Header>
    #         <RequestHeader>
    #         <MessageKey>
    #         <RequestUUID>{uuid}</RequestUUID>
    #         <ServiceRequestId>XferTrnAdd</ServiceRequestId>
    #         <ServiceRequestVersion>10.2</ServiceRequestVersion>
    #         <ChannelId>COR</ChannelId>
    #         <LanguageId/>
    #         </MessageKey>
    #         <RequestMessageInfo>
    #         <BankId>{bankid}</BankId>
    #         <TimeZone/>
    #         <EntityId/>
    #         <EntityType/>
    #         <ArmCorrelationId/>
    #         <MessageDateTime>{msgdatetime}</MessageDateTime>
    #         </RequestMessageInfo>
    #         <Security>
    #         <Token>
    #         <PasswordToken>
    #         <UserId/>
    #         <Password/>
    #         </PasswordToken>
    #         </Token>
    #         <FICertToken/>
    #         <RealUserLoginSessionId/>
    #         <RealUser/>
    #         <RealUserPwd/>
    #         <SSOTransferToken/>
    #         </Security>
    #         </RequestHeader>
    #         </Header>
    #         <Body>
    #         <XferTrnAddRequest>
    #         <XferTrnAddRq>
    #         <XferTrnHdr>
    #         <TrnType>T</TrnType>
    #         <TrnSubType>CI</TrnSubType>
    #         </XferTrnHdr>©
    #         <XferTrnDetail>
    #     """.format(uuid="161945234234", bankid="01", msgdatetime="2021-03-13T11:15:08.528")
    pd = str(posting_date).split(" ")[0]+"T"+str(posting_date).split(" ")[1]+".000"
    return(str(doc.header).format(uuid=cbs_entry.name, bankid="01", msgdatetime=pd))




@frappe.whitelist()
def encrypt_credential(api):
    doc = frappe.get_doc("API Detail", str(api))
    url = doc.api_link
    user_id = password = ""
    for a in doc.item:
        if a.param == "user_id":
            user_id = a.defined_value
        elif a.param == "password":
            password = a.defined_value
    header_string = str(user_id)+":"+str(password)
    header_bytes = header_string.encode("utf-8")
    return header_bytes, url

@frappe.whitelist()
def intra_payment(from_acc, trans_amount, promo_no, to_acc, unique_transaction_no):
    if not frappe.db.get_value('Bank Payment Settings', "BOBL", 'enable_one_to_one'):
        return
    '''
    doc = frappe.get_doc("API Detail", "ONE TO ONE - INTRA BANK")
    url = doc.api_link
    for a in doc.item:
        if a.param == "user_id":
            user_id = a.defined_value
        elif a.param == "password":
            password = a.defined_value
    '''
    header_credential, url = encrypt_credential(api="ONE TO ONE - INTRA BANK")

    payload="""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v1="http://BaNCS.TCS.com/webservice/TransferDepositAccountFundSecuredInterface/v1" xmlns:ban="http://TCS.BANCS.Adapter/BANCSSchema">			
        <soapenv:Header/>			
        <soapenv:Body>			
            <v1:transferDepositAccountFundSecured>			
                <DepAcctFundXferRq>			
                    <ban:RqHeader>			
                    <!--Optional:-->			
                    <ban:Filler1></ban:Filler1>			
                    <!--Optional:-->			
                    <ban:MsgLen></ban:MsgLen>			
                    <!--Optional:-->			
                    <ban:Filler2></ban:Filler2>			
                    <!--Optional:-->			
                    <ban:MsgTyp></ban:MsgTyp>			
                    <!--Optional:-->			
                    <ban:Filler3></ban:Filler3>			
                    <!--Optional:-->			
                    <ban:CycNum></ban:CycNum>			
                    <!--Optional:-->			
                    <ban:MsgNum></ban:MsgNum>			
                    <!--Optional:-->			
                    <ban:SegNum></ban:SegNum>			
                    <!--Optional:-->			
                    <ban:SegNum2></ban:SegNum2>			
                    <!--Optional:-->			
                    <ban:FrontEndNum></ban:FrontEndNum>			
                    <!--Optional:-->			
                    <ban:TermlNum></ban:TermlNum>			
                    <!--Optional:-->			
                        <ban:InstNum>003</ban:InstNum>			
                    <ban:BrchNum>00010</ban:BrchNum>			
                    <!--Optional:-->			
                    <ban:WorkstationNum></ban:WorkstationNum>			
                    <!--Optional:-->			
                    <ban:TellerNum>8885</ban:TellerNum>			
                    <!--Optional:-->			
                    <ban:TranNum></ban:TranNum>			
                    <!--Optional:-->			
                    <ban:JrnlNum></ban:JrnlNum>			
                    <!--Optional:-->			
                    <ban:HdrDt></ban:HdrDt>			
                    <!--Optional:-->			
                    <ban:Filler4></ban:Filler4>			
                    <!--Optional:-->			
                    <ban:Filler5></ban:Filler5>			
                    <!--Optional:-->			
                    <ban:Filler6></ban:Filler6>			
                    <!--Optional:-->			
                    <ban:Flag1></ban:Flag1>			
                    <!--Optional:-->			
                    <ban:Flag2></ban:Flag2>			
                    <!--Optional:-->			
                    <ban:Flag3></ban:Flag3>			
                    <!--Optional:-->			
                    <ban:Flag4>W</ban:Flag4>			
                    <ban:Flag5>Y</ban:Flag5>			
                    <!--Optional:-->			
                    <ban:Flag6></ban:Flag6>			
                    <!--Optional:-->			
                    <ban:Flag7></ban:Flag7>			
                    <!--Optional:-->			
                    <ban:SprvsrID></ban:SprvsrID>			
                    <!--Optional:-->			
                    <ban:SupDate></ban:SupDate>			
                    <!--Optional:-->			
                    <ban:CheckerID1></ban:CheckerID1>			
                    <!--Optional:-->			
                    <ban:ParentBlinkJrnlNum></ban:ParentBlinkJrnlNum>			
                    <!--Optional:-->			
                    <ban:CheckerID2></ban:CheckerID2>			
                    <!--Optional:-->			
                    <ban:BlinkJrnlNum></ban:BlinkJrnlNum>			
                    <ban:UUIDSource></ban:UUIDSource>			
                    <ban:UUIDNUM></ban:UUIDNUM>			
                    <!--Optional:-->			
                    <ban:UUIDSeqNo></ban:UUIDSeqNo>			
                    </ban:RqHeader>			
                    <ban:Data>			
                    <ban:FrmAcctNum>{0}</ban:FrmAcctNum>			
                    <ban:Amt>{1}</ban:Amt>			
                    <ban:PromoNum>{2}</ban:PromoNum>			
                    <ban:ToAcctNum>{3}</ban:ToAcctNum>
                            
                    <!--Optional:-->			
                    <ban:TrnAmt>{1}</ban:TrnAmt>			
                            
                    <!--Optional:-->			
                    <ban:StmtNarr>{4}</ban:StmtNarr>			
                            
                    </ban:Data>			
                </DepAcctFundXferRq>			
            </v1:transferDepositAccountFundSecured>			
        </soapenv:Body>			
        </soapenv:Envelope>""".format(from_acc, trans_amount, promo_no, to_acc, unique_transaction_no)
    '''
    headers = {
    'Authorization': 'Basic %s' % base64.b64encode(header_credential),
    'Content-Type': 'application/xml'
    }
    '''
    headers = {
    'Authorization': 'Basic RVBBWVRUUDpwYXNzd29yZDEyMyQ=',
    'Content-Type': 'application/xml'
    }
    
    response = requests.request("POST", url, headers=headers, data=payload)
    
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'ns2': 'http://TCS.BANCS.Adapter/BANCSSchema',
        'ns3': 'http://BaNCS.TCS.com/webservice/TransferDepositAccountFundSecuredInterface/v1'
    }

    JrnlNum=""
    errorMessage=""
    successMessage= ""
    message = ""
    status = ""
    dom = ElementTree.fromstring(response.text)
    for name in dom.findall('./soap:Body/ns3:transferDepositAccountFundSecuredResponse/DepAcctFundXferRs/ns2:RsHeader/ns2:JrnlNum', namespaces):
        JrnlNum = name.text
    for name in dom.findall('./soap:Body/ns3:transferDepositAccountFundSecuredResponse/DepAcctFundXferRs/ns2:Stat/ns2:ErrorMessage/ns2:ErrorMessage', namespaces):
        errorMessage = name.text
    for name in dom.findall('./soap:Body/ns3:transferDepositAccountFundSecuredResponse/DepAcctFundXferRs/ns2:Stat/ns2:OkMessage/ns2:RcptData', namespaces):
        successMessage = name.text 
    if successMessage:
        message = successMessage
        status = "Success"
    else:
        message = errorMessage
        status = "Failed"

    return {"jrnl_no":JrnlNum, "status":status, "message":message}

@frappe.whitelist()
def inter_payment(Amt, PayeeAcctNum, BnfcryAcct, BnfcryName, BnfcryAcctTyp, BnfcryRmrk, RemitterName, BfscCode, RemitterAcctType, PEMSRefNum):
    if not frappe.db.get_value('Bank Payment Settings', "BOBL", 'enable_one_to_one'):
        return
    '''
    doc = frappe.get_doc("API Detail", "ONE TO ONE - INTER BANK")
    url = doc.api_link
    for a in doc.item:
        if a.param == "user_id":
            user_id = a.defined_value
        elif a.param == "password":
            password = a.defined_value
    '''
    header_credential, url = encrypt_credential(api="ONE TO ONE - INTER BANK")

    if Amt > 1000000:
        ModeOfPmt = str("01")
    else:
        ModeOfPmt = str("02")   
    #url = "http://10.30.30.195:8888/OutwardDebit/OutwardDebitInterfaceHttpService"
    payload="""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v1="http://BaNCS.TCS.com/webservice/OutwardDebitInterface/v1" xmlns:ban="http://TCS.BANCS.Adapter/BANCSSchema">
            <soapenv:Header/>
            <soapenv:Body>
                <v1:outwardDebit>
                    <OutwardDrRq>
                        <ban:RqHeader>
                        <!--Optional:-->
                        <ban:Filler1></ban:Filler1>
                        <!--Optional:-->
                        <ban:MsgLen></ban:MsgLen>
                        <!--Optional:-->
                        <ban:Filler2></ban:Filler2>
                        <!--Optional:-->
                        <ban:MsgTyp></ban:MsgTyp>
                        <!--Optional:-->
                        <ban:Filler3></ban:Filler3>
                        <!--Optional:-->
                        <ban:CycNum></ban:CycNum>
                        <!--Optional:-->
                        <ban:MsgNum></ban:MsgNum>
                        <!--Optional:-->
                        <ban:SegNum></ban:SegNum>
                        <!--Optional:-->
                        <ban:SegNum2></ban:SegNum2>
                        <!--Optional:-->
                        <ban:FrontEndNum></ban:FrontEndNum>
                        <!--Optional:-->
                        <ban:TermlNum></ban:TermlNum>
                        <!--Optional:-->
                        <ban:InstNum>003</ban:InstNum>
                        <ban:BrchNum>00010</ban:BrchNum>
                        <!--Optional:-->
                        <ban:WorkstationNum></ban:WorkstationNum>
                        <!--Optional:-->
                        <ban:TellerNum>8885</ban:TellerNum>
                        <!--Optional:-->
                        <ban:TranNum></ban:TranNum>
                        <!--Optional:-->
                        <ban:JrnlNum></ban:JrnlNum>
                        <!--Optional:-->
                        <ban:HdrDt></ban:HdrDt>
                        <!--Optional:-->
                        <ban:Filler4></ban:Filler4>
                        <!--Optional:-->
                        <ban:Filler5></ban:Filler5>
                        <!--Optional:-->
                        <ban:Filler6></ban:Filler6>
                        <!--Optional:-->
                        <ban:Flag1></ban:Flag1>
                        <!--Optional:-->
                        <ban:Flag2></ban:Flag2>
                        <!--Optional:-->
                        <ban:Flag3></ban:Flag3>
                        <!--Optional:-->
                        <ban:Flag4>W</ban:Flag4>
                        <ban:Flag5>Y</ban:Flag5>
                        <!--Optional:-->
                        <ban:Flag6></ban:Flag6>
                        <!--Optional:-->
                        <ban:Flag7></ban:Flag7>
                        <!--Optional:-->
                        <ban:SprvsrID></ban:SprvsrID>
                        <!--Optional:-->
                        <ban:SupDate></ban:SupDate>
                        <!--Optional:-->
                        <ban:CheckerID1></ban:CheckerID1>
                        <!--Optional:-->
                        <ban:ParentBlinkJrnlNum></ban:ParentBlinkJrnlNum>
                        <!--Optional:-->
                        <ban:CheckerID2></ban:CheckerID2>
                        <!--Optional:-->
                        <ban:BlinkJrnlNum></ban:BlinkJrnlNum>
                        <ban:UUIDSource></ban:UUIDSource>
                        <ban:UUIDNUM></ban:UUIDNUM>
                        <!--Optional:-->
                        <ban:UUIDSeqNo></ban:UUIDSeqNo>
                        </ban:RqHeader>
                        <ban:Data>
                        <ban:ModeOfPmt>{0}</ban:ModeOfPmt>
                        <ban:Amt>{1}</ban:Amt>
                        <ban:PayeeAcctNum>{2}</ban:PayeeAcctNum>
                        <ban:BnfcryAcct>{3}</ban:BnfcryAcct>
                        <ban:BnfcryName>{4}</ban:BnfcryName>
                        <ban:BnfcryAcctTyp>{5}</ban:BnfcryAcctTyp>
                        <!--Optional:-->
                        <ban:BnfcryRmrk>{6}</ban:BnfcryRmrk>
                        <!--Optional:-->
                        <ban:RemitterRmrk>{6}</ban:RemitterRmrk>
                        <ban:RemitterName>{7}</ban:RemitterName>
                        <ban:BfscCode>{8}</ban:BfscCode>
                        <ban:BnfcryAmt>{1}</ban:BnfcryAmt>
                        <ban:RemitterAcctTyp>{9}</ban:RemitterAcctTyp>
                        <ban:SndToRcvrInfo>{6}</ban:SndToRcvrInfo>
                        <!--Optional:-->
                        <ban:SndToRcvrInfo1></ban:SndToRcvrInfo1>
                        <!--Optional:-->
                        <ban:SndToRcvrInfo2></ban:SndToRcvrInfo2>
                        <ban:Comsn>0</ban:Comsn>
                        <ban:TtlAmt>{1}</ban:TtlAmt>
                        <ban:TxnCurrCode1>BTN</ban:TxnCurrCode1>
                        <!--Optional:-->
                        <ban:Amount3></ban:Amount3>
                        <!--Optional:-->
                        <ban:EmailID></ban:EmailID>
                        <ban:RemitterAcctNum>{2}</ban:RemitterAcctNum>
                        <ban:PEMSRefNum>{10}</ban:PEMSRefNum>
                        </ban:Data>
                    </OutwardDrRq>
                </v1:outwardDebit>
            </soapenv:Body>
        </soapenv:Envelope>""".format(ModeOfPmt, Amt, PayeeAcctNum, BnfcryAcct, BnfcryName, BnfcryAcctTyp, BnfcryRmrk, RemitterName, BfscCode, RemitterAcctType, PEMSRefNum)
    headers = {
    'Authorization': 'Basic RVBBWVRUUDpwYXNzd29yZDEyMyQ=',
    'Content-Type': 'application/xml'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    from xml.etree import ElementTree

    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'ns2': 'http://TCS.BANCS.Adapter/BANCSSchema',
        'ns3': 'http://BaNCS.TCS.com/webservice/OutwardDebitInterface/v1'
    }

    JrnlNum=""
    errorMessage=""
    successMessage= ""
    dom = ElementTree.fromstring(response.text)
    for name in dom.findall('./soap:Body/ns3:outwardDebitResponse/OutwardDrRs/ns2:RsHeader/ns2:JrnlNum', namespaces):
        JrnlNum = name.text
    for name in dom.findall('./soap:Body/ns3:outwardDebitResponse/OutwardDrRs/ns2:Stat/ns2:ErrorMessage/ns2:ErrorMessage', namespaces):
        errorMessage = name.text
    for name in dom.findall('./soap:Body/ns3:outwardDebitResponse/OutwardDrRs/ns2:Stat/ns2:OkMessage/ns2:RcptData', namespaces):
        successMessage = name.text

    if successMessage:
        message = successMessage
        status = "Success"
    else:
        message = errorMessage
        status = "Failed"

    return {"jrnl_no":JrnlNum, "status":status, "message":message}

@frappe.whitelist()
def inr_remittance(AcctNum, Amt, BnfcryAcct, BnfcryName, BnfcryAddr1, IFSC, BankCode, PurpCode, RemittersName, RemittersAddr1, ComsnOpt, PromoCode, PemsRefNum):
    if not frappe.db.get_value('Bank Payment Settings', "BOBL", 'enable_one_to_one'):
        return
    
    header_credential, url = encrypt_credential(api="ONE TO ONE - INR Remmittance")
    '''
    doc = frappe.get_doc("API Detail", "ONE TO ONE - INR Remmittance")
    url = doc.api_link
    for a in doc.item:
        if a.param == "user_id":
            user_id = a.defined_value
        elif a.param == "password":
            password = a.defined_value
    '''
    #url = "http://10.30.30.195:8088/INRRemittanceByTransferSecured/INRRemittanceByTransferSecuredInterfaceHttpService"
    payload = """
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" 
    xmlns:v1="http://BaNCS.TCS.com/webservice/INRRemittanceByTransferSecuredInterface/v1" 
    xmlns:ban="http://TCS.BANCS.Adapter/BANCSSchema">
    <soapenv:Header/>
    <soapenv:Body>
        <v1:iNRRemittanceByTransferSecured>
            <INRRemittanceByXferRq>
                <ban:RqHeader>
                <!--Optional:-->
                <ban:Filler1></ban:Filler1>
                <!--Optional:-->
                <ban:MsgLen></ban:MsgLen>
                <!--Optional:-->
                <ban:Filler2></ban:Filler2>
                <!--Optional:-->
                <ban:MsgTyp></ban:MsgTyp>
                <!--Optional:-->
                <ban:Filler3></ban:Filler3>
                <!--Optional:-->
                <ban:CycNum></ban:CycNum>
                <!--Optional:-->
                <ban:MsgNum></ban:MsgNum>
                <!--Optional:-->
                <ban:SegNum></ban:SegNum>
                <!--Optional:-->
                <ban:SegNum2></ban:SegNum2>
                <!--Optional:-->
                <ban:FrontEndNum></ban:FrontEndNum>
                <!--Optional:-->
                <ban:TermlNum></ban:TermlNum>
                <!--Optional:-->
                    <ban:InstNum>03</ban:InstNum>
                <ban:BrchNum>00010</ban:BrchNum>
                <!--Optional:-->
                <ban:WorkstationNum></ban:WorkstationNum>
                <!--Optional:-->
                <ban:TellerNum>8882</ban:TellerNum>
                <!--Optional:-->
                <ban:TranNum></ban:TranNum>
                <!--Optional:-->
                <ban:JrnlNum></ban:JrnlNum>
                <!--Optional:-->
                <ban:HdrDt></ban:HdrDt>
                <!--Optional:-->
                <ban:Filler4></ban:Filler4>
                <!--Optional:-->
                <ban:Filler5></ban:Filler5>
                <!--Optional:-->
                <ban:Filler6></ban:Filler6>
                <!--Optional:-->
                <ban:Flag1></ban:Flag1>
                <!--Optional:-->
                <ban:Flag2></ban:Flag2>
                <!--Optional:-->
                <ban:Flag3></ban:Flag3>
                <!--Optional:-->
                <ban:Flag4>W</ban:Flag4>
                <ban:Flag5>Y</ban:Flag5>
                <!--Optional:-->
                <ban:Flag6></ban:Flag6>
                <!--Optional:-->
                <ban:Flag7></ban:Flag7>
                <!--Optional:-->
                <ban:SprvsrID></ban:SprvsrID>
                <!--Optional:-->
                <ban:SupDate></ban:SupDate>
                <!--Optional:-->
                <ban:CheckerID1></ban:CheckerID1>
                <!--Optional:-->
                <ban:ParentBlinkJrnlNum></ban:ParentBlinkJrnlNum>
                <!--Optional:-->
                <ban:CheckerID2></ban:CheckerID2>
                <!--Optional:-->
                <ban:BlinkJrnlNum></ban:BlinkJrnlNum>
                <ban:UUIDSource></ban:UUIDSource>
                <ban:UUIDNUM></ban:UUIDNUM>
                <!--Optional:-->
                <ban:UUIDSeqNo></ban:UUIDSeqNo>
                </ban:RqHeader>
            <ban:Data>
                <ban:AcctNum>{0}</ban:AcctNum>
                <!--Optional:-->
                <ban:CustName></ban:CustName>
                <!--Optional:-->
                <ban:Bal></ban:Bal>
                <!--Optional:-->
                <ban:ModeOfPay></ban:ModeOfPay>
                <ban:Amt>{1}</ban:Amt>
                <!--Optional:-->
                <ban:AmtCur></ban:AmtCur>
                <!--Optional:-->
                <ban:Comsn>2</ban:Comsn>
                <!--Optional:-->
                <ban:TtlAmt></ban:TtlAmt>
                <!--Optional:-->
                <ban:TtlAmtCur>BTN</ban:TtlAmtCur>
                <ban:BnfcryAcct>{2}</ban:BnfcryAcct>
                <ban:BnfcryName>{3}</ban:BnfcryName>
                <ban:BnfcryAddr1>{4}</ban:BnfcryAddr1>
                <!--Optional:-->
                <ban:BnfcryAddr2></ban:BnfcryAddr2>
                <!--Optional:-->
                <ban:BnfcryAddr3></ban:BnfcryAddr3>
                <ban:IFSC>{5}</ban:IFSC>
                <ban:BankCode>{6}</ban:BankCode>
                <ban:PurpCode>{7}</ban:PurpCode>
                <ban:RemittersName>{8}</ban:RemittersName>
                <ban:RemittersAddr1>{9}</ban:RemittersAddr1>
                <!--Optional:-->
                <ban:RemittersAddr2></ban:RemittersAddr2>
                <!-- Optional:-->
                <ban:RemittersAddr3></ban:RemittersAddr3>
                <ban:MailIdMobile></ban:MailIdMobile>
                <!--Optional:-->
                <ban:ComsnOpt>{10}</ban:ComsnOpt>
                <!--Optional:-->
                <ban:PromoCode>{11}</ban:PromoCode>
                <!--Optional:-->
                <ban:PemsRefNum>{12}</ban:PemsRefNum>
                </ban:Data>
            </INRRemittanceByXferRq>
        </v1:iNRRemittanceByTransferSecured>
    </soapenv:Body>""".format(AcctNum, Amt, BnfcryAcct, BnfcryName, BnfcryAddr1, IFSC, BankCode, PurpCode, RemittersName, RemittersAddr1, ComsnOpt, PromoCode, PemsRefNum)

    headers = {
    'Authorization': 'Basic RVBBWVRUUDpwYXNzd29yZDEyMyQ=',
    'Content-Type': 'application/xml'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    namespaces = {
        'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
        'ns2': 'http://TCS.BANCS.Adapter/BANCSSchema',
        'ns3': 'http://BaNCS.TCS.com/webservice/INRRemittanceByTransferSecuredInterface/v1'
    }

    JrnlNum=""
    errorMessage=""
    successMessage= ""
    dom = ElementTree.fromstring(response.text)
    for name in dom.findall('./soap:Body/ns3:iNRRemittanceByTransferSecuredResponse/INRRemittanceByXferRs/ns2:RsHeader/ns2:JrnlNum', namespaces):
        JrnlNum = name.text
    for name in dom.findall('./soap:Body/ns3:iNRRemittanceByTransferSecuredResponse/INRRemittanceByXferRs/ns2:Stat/ns2:ErrorMessage/ns2:ErrorMessage', namespaces):
        errorMessage = name.text
    for name in dom.findall('./soap:Body/ns3:iNRRemittanceByTransferSecuredResponse/INRRemittanceByXferRs/ns2:Stat/ns2:OkMessage/ns2:RcptData', namespaces):
        successMessage = name.text

    if successMessage:
        message = successMessage
        status = "Success"
    else:
        message = errorMessage
        status = "Failed"

    return {"jrnl_no":JrnlNum, "status":status, "message":message}
    
@frappe.whitelist()
def fetch_balance(account_no):
    if not account_no:
        return {"message":"Please provide account no"}
    if not frappe.db.get_value('Bank Payment Settings', "BOBL", 'enable_one_to_one'):
        return
    header_credential, url = encrypt_credential(api="BOB Customer Balance Enquiry")
    '''
    doc = frappe.get_doc("API Detail", "BOB Customer Balance Enquiry")
    url = doc.api_link
    for a in doc.item:
        if a.param == "user_id":
            user_id = a.defined_value
        elif a.param == "password":
            password = a.defined_value
    '''

    #url = "http://10.30.30.195:8088/EnquireShort/EnquireShortInterfaceHttpService"
    payload="""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v1="http://BaNCS.TCS.com/webservice/EnquireShortInterface/v1" xmlns:ban="http://TCS.BANCS.Adapter/BANCSSchema">
                <soapenv:Header/>
                <soapenv:Body>
                    <v1:enquireShort>
                        <ShrtInqRq>
                            <ban:RqHeader>
                            <!--Optional:-->
                            <ban:Filler1></ban:Filler1>
                            <!--Optional:-->
                            <ban:MsgLen></ban:MsgLen>
                            <!--Optional:-->
                            <ban:Filler2></ban:Filler2>
                            <!--Optional:-->
                            <ban:MsgTyp></ban:MsgTyp>
                            <!--Optional:-->
                            <ban:Filler3></ban:Filler3>
                            <!--Optional:-->
                            <ban:CycNum></ban:CycNum>
                            <!--Optional:-->
                            <ban:MsgNum></ban:MsgNum>
                            <!--Optional:-->
                            <ban:SegNum></ban:SegNum>
                            <!--Optional:-->
                            <ban:SegNum2></ban:SegNum2>
                            <!--Optional:-->
                            <ban:FrontEndNum></ban:FrontEndNum>
                            <!--Optional:-->
                            <ban:TermlNum></ban:TermlNum>
                            <!--Optional:-->
                            <ban:InstNum>003</ban:InstNum>
                            <ban:BrchNum>00010</ban:BrchNum>
                            <!--Optional:-->
                            <ban:WorkstationNum></ban:WorkstationNum>
                            <!--Optional:-->
                            <ban:TellerNum>8885</ban:TellerNum>
                            <!--Optional:-->
                            <ban:TranNum></ban:TranNum>
                            <!--Optional:-->
                            <ban:JrnlNum></ban:JrnlNum>
                            <!--Optional:-->
                            <ban:HdrDt></ban:HdrDt>
                            <!--Optional:-->
                            <ban:Filler4></ban:Filler4>
                            <!--Optional:-->
                            <ban:Filler5></ban:Filler5>
                            <!--Optional:-->
                            <ban:Filler6></ban:Filler6>
                            <!--Optional:-->
                            <ban:Flag1></ban:Flag1>
                            <!--Optional:-->
                            <ban:Flag2></ban:Flag2>
                            <!--Optional:-->
                            <ban:Flag3></ban:Flag3>
                            <!--Optional:-->
                            <ban:Flag4>W</ban:Flag4>
                            <ban:Flag5>Y</ban:Flag5>
                            <!--Optional:-->
                            <ban:Flag6></ban:Flag6>
                            <!--Optional:-->
                            <ban:Flag7></ban:Flag7>
                            <!--Optional:-->
                            <ban:SprvsrID></ban:SprvsrID>
                            <!--Optional:-->
                            <ban:SupDate></ban:SupDate>
                            <!--Optional:-->
                            <ban:CheckerID1></ban:CheckerID1>
                            <!--Optional:-->
                            <ban:ParentBlinkJrnlNum></ban:ParentBlinkJrnlNum>
                            <!--Optional:-->
                            <ban:CheckerID2></ban:CheckerID2>
                            <!--Optional:-->
                            <ban:BlinkJrnlNum></ban:BlinkJrnlNum>
                            <ban:UUIDSource></ban:UUIDSource>
                            <ban:UUIDNUM></ban:UUIDNUM>
                            <!--Optional:-->
                            <ban:UUIDSeqNo></ban:UUIDSeqNo>
                            </ban:RqHeader>
                            <ban:Data>
                            <ban:AcctNum>{}</ban:AcctNum>
                            </ban:Data>
                        </ShrtInqRq>
                    </v1:enquireShort>
                </soapenv:Body>
                </soapenv:Envelope>""".format(account_no)

    headers = {
    'Authorization': 'Basic RVBBWVRUUDpwYXNzd29yZDEyMyQ=',
    'Content-Type': 'application/xml'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=5)
        from xml.etree import ElementTree
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns2': 'http://TCS.BANCS.Adapter/BANCSSchema',
            'ns3': 'http://BaNCS.TCS.com/webservice/EnquireShortInterface/v1'
        }

        dom = ElementTree.fromstring(response.text)

        for name in dom.findall('./soap:Body/ns3:enquireShortResponse/ShrtInqRs/ns2:ShrtInqData/ns2:AcctName', namespaces):
            account_holder = name.text

        for name in dom.findall('./soap:Body/ns3:enquireShortResponse/ShrtInqRs/ns2:ShrtInqData/ns2:AvailBal', namespaces):
            avail_bal = name.text

        balance_amt = avail_bal.replace(" CR","")
        return {'status':'0','account_holder':account_holder, "balance_amount":balance_amt, "message": "Success"}
    except requests.exceptions.RequestException as err:
        return {'status':'1', 'message':'Respomnse time out', 'error': err}
