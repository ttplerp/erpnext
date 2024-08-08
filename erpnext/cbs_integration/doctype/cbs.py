# -*- coding: utf-8 -*-
# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, flt, now, get_bench_path, get_site_path, touch_file, getdate, get_datetime, add_days
from frappe.model.document import Document
from erpnext.integrations.bps import SftpClient
from erpnext.integrations.bank_api import intra_payment, inter_payment, inr_remittance, fetch_balance
import datetime
import os
from frappe.model.naming import make_autoname
import csv
from frappe.model.mapper import get_mapped_doc
import traceback
import oracledb
import logging
import json
from time import sleep

# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
# logger = logging.getLogger(__name__)

# def ResultIter(cursor, arraysize=100):
#     while True:
#         results = cursor.fetchmany(arraysize)
#         if not results:
#             break
#         for result in results:
#             yield result

class CBS:
    def __init__(self):
        settings = frappe.get_single('CBS Connectivity')
        db_host = settings.host
        db_port = settings.port
        db_usr = settings.username
        db_pwd = settings.get_password('password')
        db_db = settings.database


        try:
            self.dsn = f"{db_host}:{db_port}/{db_db}"
            self.con = oracledb.connect(user=db_usr, password=db_pwd, dsn=self.dsn)
            self.cursor = self.con.cursor()
            frappe.logger().info('*** Connected to CBS successfully...')
        except oracledb.DatabaseError as error:
            frappe.logger().exception('Failed to connect to CBS: {0}'.format(error))
            raise  
			
    def close_connection(self):
        # Close the cursor and the connection
        if self.cursor:
            self.cursor.close()
        if self.con:
            self.con.close()
        frappe.logger().info('*** Disconnected from CBS successfully...')

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except oracledb.DatabaseError as error:
            frappe.logger().exception('Failed to execute query: {0}'.format(error))
            raise

@frappe.whitelist()
def test_connectivity():
    db = None  
    try:
        db = CBS()  
        query = "select * from v$version"
        res = db.execute_query(query)
        frappe.msgprint(_("{}").format(res[0][0]), title="Connection Successful")
    except Exception as e:
        frappe.throw(_("Unable to connect to CBS: " + str(e)), title="Connection Failure")
    finally:
        if db:
            db.close_connection() 
