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

def get_gl_type_map():
	return {
		'CASA': {'DR' : '51', 'CR' : '01'},
		'GL': {'DR' : '54', 'CR' : '04'}
	}

def get_data(doctype=None, docname=None, doclist=None, from_date=None, to_date=None):
	if doctype and docname:
		status = {0 : 'Draft', 1 : 'Submitted', 2 : 'Cancelled'}
		docstatus = frappe.db.get_value(doctype, docname, "docstatus")
		if docstatus != 1:
			frappe.throw(_("You cannot process payment for transactions in <b>{}</b> status").format(status[docstatus]))

	data = []
	gl_type_map = get_gl_type_map()
	gl_entries = get_gl_entries(doctype, docname, doclist, from_date, to_date)
	for i in gl_entries:
		dr_cr_list = {'DR': i.debit, 'CR': i.credit}
		for dr_cr in dr_cr_list:
			gl_type_cd = None
			if dr_cr_list[dr_cr] > 0:
				gl_type_cd = gl_type_map[i.gl_type][dr_cr] if i.gl_type in ('CASA', 'GL') else None
			else:
				continue

			if i.gl_type == 'CASA':
				partylist_json = json.loads(i.partylist_json) if i.partylist_json else None
				if dr_cr == 'CR' and partylist_json:
					for party_type in partylist_json:
						for party in partylist_json[party_type]:
							rec = get_formatted_record(i, gl_type_cd, dr_cr_list, dr_cr, frappe._dict(party))
							data.append(rec)
				else:
					rec = get_formatted_record(i, gl_type_cd, dr_cr_list, dr_cr)
					data.append(rec)
			else:
				rec = get_formatted_record(i, gl_type_cd, dr_cr_list, dr_cr)
				data.append(rec)
	return data

def get_gl_entries(doctype, docname, doclist, from_date, to_date):
	company_branch_code = '09990'
	cond = get_conditions(doctype, docname, doclist, from_date, to_date)
	res = frappe.db.sql("""select t1.name gl_name, t1.voucher_type, t1.voucher_no,
				t1.account, a.account_number, t1.account_currency,
				t1.cost_center,
				t1.party_type, t1.party,
				t1.debit, t1.debit_in_account_currency, 
				t1.credit, t1.credit_in_account_currency,
				t1.posting_date, ifnull(a.gl_type,'GL') gl_type, a.initiating_branch, 
    			a.bank_name, a.bank_branch, 
				a.bank_account_type, a.bank_account_no,
				replace(t1.remarks,"\n",",") remarks, t1.partylist_json,
				null as cbs_entry
			from `tabGL Entry` t1
			inner join `tabAccount` a on a.name = t1.account
			inner join `tabTransaction Mapping` t2 on t2.name = t1.voucher_type and t2.transaction_type in ('CASA', 'GL')
			left join `tabCurrency` c on c.name = a.account_currency
			{cond}
			and t1.cbs_enabled = 1
			and t1.is_cancelled = 0
			and not exists(select 1
				from `tabCBS Entry Upload` ceu
				where ceu.gl_entry = t1.name
				and ceu.docstatus != 2)
		order by posting_date, voucher_type, voucher_no""".format(cond=cond, company_branch_code=company_branch_code), as_dict=True)

	# update gl entries with branch_code
	for i in res:
		branch_code = get_branch_code(gl_entry=i)
		i.update({'branch_code': branch_code})
	return res

def get_conditions(doctype, docname, doclist, from_date, to_date):
	cond = []
	if doctype and docname:
		cond.append('t1.voucher_type = "{}" and t1.voucher_no = "{}"'.format(doctype, docname))
	elif doclist:
		cond2 = []
		for doctype,docname in doclist.items():
			if len(docname) == 1:
				cond2.append('(t1.voucher_type = "{}" and t1.voucher_no="{}")'.format(doctype,docname[0]))
			else:
				cond2.append('(t1.voucher_type = "{}" and t1.voucher_no in {})'.format(doctype,tuple(docname)))
		cond.append('({})'.format(" or ".join(cond2)))
	else:
		if from_date and to_date:
			if from_date == to_date:
				cond.append("t1.posting_date = '{}'".format(from_date))
			else:
				cond.append("t1.posting_date between '{}' and '{}'".format(from_date, to_date))

		if doctype:
			cond.append('t1.voucher_type = "{}"'.format(doctype))
		if docname:
			cond.append('t1.voucher_no = "{}"'.format(docname))
		
	if cond:
		cond = " where " + " and ".join(cond)
	return cond

def get_branch_code(gl_entry):
	company_branch_code, branch_code = "00000", None
	if gl_entry.gl_type == "CASA":
		branch_code = '00000'
	else:
		if gl_entry.initiating_branch == "Self Branch":
			bl = frappe.db.sql("""select distinct b.branch_code
						from `tabBranch` b
						where b.cost_center = "{}"
					""".format(gl_entry.cost_center))
			if bl:
				branch_code = bl[0][0]
		else:
			branch_code = company_branch_code

	branch_code  = branch_code[-4:] if branch_code else branch_code
	return branch_code

def get_formatted_record(gl, gl_type_cd, dr_cr_list, dr_cr, party=None):
	res = frappe._dict()
	error = []
	processing_branch = '9990'
	account_number = None
	amount = 0
	gl_type = str(gl.gl_type)
	remarks = ""
	if gl.gl_type == 'CASA':
		bank_details = ()
		if party:
			gl_type = 'CASA TO PARTY'
			if party.get('recovery_account') and not (party.get('bank_name') == "BDBL" and party.get('account_number')):
				error.append("Invalid Bank Recovery Details for {}".format(frappe.get_desk_link(party.get('party_type'), party.get('party'))))				
			elif party.get('bank_name') == 'BDBL' and party.get('account_number'):
				account_number = party.get('account_number')
				if party.get('recovery_account'):	# Loan credit used only for Payroll Entry
					gl_type_cd = "03"
			else:
				if party.get('party_type') == 'Supplier':
					bank_details = frappe.db.get_value('Supplier', party.get('party'), ['bank_name', 'account_number', 'bank_account_type'])
				elif party.get('party_type') == 'Employee':
					bank_details = frappe.db.get_value('Employee', party.get('party'), ['bank_name', 'bank_ac_no', 'bank_account_type'])

				if not bank_details or not bank_details[0] or not bank_details[1]:
					error.append("Invalid Bank Details for Beneficiary {}".format(frappe.get_desk_link(party.get('party_type'), party.get('party'))))
				else:
					if bank_details[0] == 'BDBL':
						account_number = bank_details[1]
						if bank_details[2] and bank_details[2] == "04":
							gl_type_cd = "03"
					else:
						error.append("Invalid Bank Details for Beneficiary {}".format(frappe.get_desk_link(party.get('party_type'), party.get('party'))))
			if party.get('remarks'):
				remarks = party.get('remarks')
			amount = round(flt(party.get('amount')),2)
		else:
			gl_type = 'CASA TO BANK'
			bank_details = frappe.db.get_value('Account', gl.account, ['bank_name', 'bank_account_no'])
			if not bank_details or not bank_details[0] or not bank_details[1]:
				error.append("Invalid Bank Account Details for {}".format(frappe.get_desk_link('Account', gl.account)))
			else:
				if bank_details[0] == 'BDBL':
					account_number = bank_details[1]
			amount = round(flt(gl.debit if dr_cr == 'DR' else gl.credit),2)			
		res.update({"gl_entry": gl.gl_name, "voucher_type": gl.voucher_type, "voucher_no": gl.voucher_no, 
					"account": gl.account, "debit": amount if dr_cr == 'DR' else 0, "credit": amount if dr_cr == 'CR' else 0})
	else:
		# validate initiating branch
		if not gl.branch_code:
			error.append("Initiating Branch Code is missing")

		# extract account number
		account_number = None
		if not gl.account_number:
			error.append("Account Number not found for {}".format(frappe.get_desk_link('Account',gl.account)))
		else:
			if str(gl.account_number).split()[0].isdigit():
				account_number = str(gl.account_number).split()[0]
			else:
				error.append("Account Number should be numeric for {}".format(frappe.get_desk_link('Account',gl.account)))
		amount = round(flt(dr_cr_list[dr_cr]),2)
		res.update({"gl_entry": gl.gl_name, "voucher_type": gl.voucher_type, "voucher_no": gl.voucher_no, 
					"account": gl.account, "debit": gl.debit, "credit": gl.credit})
    
	remarks = str(gl.remarks if gl.remarks else '').strip().strip('\n') + " "+remarks
	res.update({"gl_type_cd": gl_type_cd or '', "branch_code": gl.branch_code or '', "currency_code": gl.currency_code or '',
			"account_number": account_number or '', "segment_code": gl.segment_code or '', "amount": amount,
			"remarks": remarks or '', "processing_branch": processing_branch or '', "posting_date": str(gl.posting_date),
			"error": ", ".join(error) or '', "gl_type": gl_type or ''})
	return res
