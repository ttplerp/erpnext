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
def td_account_inq(td_account_no=None):
    if not td_account_no:
        return
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    #url = "https://was1-dc-srv.bdbl.bt:11300/FISERVLET/fihttp"
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.SSL_CIPHER_LIST, 'HIGH:!aNULL:!MD5')
    c.setopt(c.TIMEOUT, 500)
    c.setopt(c.SSLVERSION, pycurl.SSLVERSION_TLSv1)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.SSL_VERIFYPEER, 0)
    payload="""<FIXML xsi:schemaLocation="http://www.finacle.com/fixml BalInq.xsd"
                xmlns="http://www.finacle.com/fixml"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <Header>
                    <RequestHeader>
                        <MessageKey>
                            <RequestUUID>509175659618</RequestUUID>
                            <ServiceRequestId>BalInq</ServiceRequestId>
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
                            <MessageDateTime>2026-03-10T09:22:51.457</MessageDateTime>
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
                    <BalInqRequest>
                        <BalInqRq>
                            <AcctId>
                                <AcctId>{0}</AcctId>
                            </AcctId>
                        </BalInqRq>
                    </BalInqRequest>
                </Body>
            </FIXML>""".format(td_account_no)

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
        actual_amt = flt(root.find('.//ns:clrBalAmt', namespaces=namespace).text,2)
        return actual_amt
    except:
        return {"msg":"No Account Found"}

@frappe.whitelist()
def td_closure(td_account_no=None, credit_account=None, uuid=None, pd=None):
    if not td_account_no or not credit_account:
        return

    #Fetch the Clear Amount
    actual_amt = td_account_inq(td_account_no)
    buffer = BytesIO()
    doc = frappe.get_doc("API Detail","MULTI LEDGER")
    url = str(doc.api_link)
    #url = "https://bdbl-fcstaging-uat.bdbl.bt:11000/FISERVLET/fihttp"
    #url = "https://bdbl-was-srv01.bdbl.bt:10300/FISERVLET/fihttp"
    #url = "https://was1-dc-srv.bdbl.bt:11300/FISERVLET/fihttp"
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
                <FIXML xsi:schemaLocation="http://www.finacle.com/fixml DepAcctClose.xsd" xmlns="http://www.finacle.com/fixml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <Header>
                        <RequestHeader>
                            <MessageKey>
                                <RequestUUID>{3}</RequestUUID>
                                <ServiceRequestId>DepAcctClose</ServiceRequestId>
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
                                <MessageDateTime>{4}</MessageDateTime>
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
                        <DepAcctCloseRequest>
                            <DepAcctCloseRq>
                                <DepAcctId>
                                    <AcctId>{0}</AcctId>
                                </DepAcctId>
                                <RepayAcctId>
                                    <AcctId>{1}</AcctId>
                                </RepayAcctId>
                                <CloseModeFlg>N</CloseModeFlg>
                            </DepAcctCloseRq>
                            <DepAcctClose_CustomData>
                                <PENALINTFLG>N</PENALINTFLG>
                                <WITHDRAWAMT>{2}</WITHDRAWAMT>
                                <WITHDRAWCRNCY>BTN</WITHDRAWCRNCY>
                            </DepAcctClose_CustomData>
                        </DepAcctCloseRequest>
                    </Body>
            </FIXML>""".format(td_account_no, credit_account, actual_amt, uuid, pd)

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
    error_desc = ""
    error_desc = root.find(".//fixml:ErrorDetail/fixml:ErrorDesc", ns)
    #print(status, error_desc.text)
    msg = error_desc.text if status == "FAILURE" else ""
    return {
        "status": str(status),
        "msg": str(msg)
    }
    
