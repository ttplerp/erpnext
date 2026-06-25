# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr, rounded
from erpnext.accounts.report.financial_statements \
	import filter_accounts, set_gl_entries_by_account, filter_out_zero_value_rows

def execute(filters=None):
	columns = get_columns()
	data = get_accounts(filters)
	return columns, data

def get_accounts(filters):
	data = []
	for a in frappe.db.sql("""SELECT a.name, b.fixed_asset_account as fa, b.accumulated_depreciation_account as acc, 
								b.depreciation_expense_account as dep from `tabAsset Category` a, 
							`tabAsset Category Account` b 
							where a.name = b.parent""", 
							as_dict=True):
		gross_opening = get_values(a.fa, filters.to_date, filters.from_date, filters.cost_center, opening=True)[0]
		gross = get_values(a.fa, filters.to_date, filters.from_date, filters.cost_center)[0]
		dep_opening = get_values(a.acc, filters.to_date, filters.from_date, filters.cost_center, opening=True)[0]
		acc_dep = get_values(a.acc, filters.to_date, filters.from_date, filters.cost_center)[0]
		# following line commented by SHIV on 2021/03/10 as it is not used anywhere
		#dep = get_values(a.dep, filters.to_date, filters.from_date, filters.cost_center)[0]
		adj = get_values(a.acc, filters.to_date, filters.from_date, filters.cost_center, adjustment=True)[0]		

		g_open = flt(gross_opening.debit) - flt(gross_opening.credit)
		g_addition = flt(gross.debit)
		g_adjustment = flt(gross.credit)
		g_total = g_open + g_addition - g_adjustment
		#frappe.msgprint(str(dep_opening.debit)+" "+str(dep_opening.credit))
		d_open = -1 * (flt(dep_opening.debit) - flt(dep_opening.credit))
		dep_adjust = flt(acc_dep.debit)
		adj_adjust = flt(adj.credit)
		dep_addition = flt(acc_dep.credit) - flt(adj.credit)
		dep_add = flt(acc_dep.credit)
		d_total = d_open + dep_add  - flt(dep_adjust)
		
		income_tax = frappe.db.sql("""select  sum(b.depreciation_amount) as total_income_tax
										from `tabAsset` a, `tabDepreciation Schedule` b
										where a.name = b.parent
											and a.asset_category = '{0}'
											and b.schedule_date between '{1}' and '{2}'
											and a.docstatus = 1
											and (
												a.status not in ('Scrapped', 'Sold')
												OR
												(a.status in ('Scrapped', 'Sold') AND a.disposal_date >= '{1}' and b.schedule_date <= a.disposal_date)
											)
									""".format(a.name, filters.from_date, filters.to_date), as_dict=True)

		opening_it_dep = frappe.db.sql("""
								select sum(acc_income_tax) acc_income_tax, sum(depreciation_income_tax) depreciation_income_tax
								 	from (select 
												sum(b.accumulated_depreciation_amount) as acc_income_tax,
												sum(b.depreciation_amount) as depreciation_income_tax
							   			from `tabAsset` a, `tabDepreciation Schedule` b
						 	 			where a.name = b.parent
						  					and a.asset_category = '{0}'
						  					and '{1}' between b.schedule_start_date and b.schedule_date and b.depreciation_amount > 0
											and a.docstatus = 1
											and (
												a.status not in ('Scrapped', 'Sold')
												OR
												(a.status in ('Scrapped', 'Sold') AND a.disposal_date >= '{1}' and b.schedule_date <= a.disposal_date)
											)
								 			and b.depreciation_amount > 0
								 
								 		union
								 
								 		select 
												sum(b.accumulated_depreciation_amount) as acc_income_tax,
												0 as depreciation_income_tax
							   			from `tabAsset` a, `tabDepreciation Schedule` b
						 	 			where a.name = b.parent
						  					and a.asset_category = '{0}'
						  					and ((b.schedule_date < '{1}' 
													and 
												b.schedule_date = (select max(c.schedule_date) 
																	from `tabDepreciation Schedule` c
																	where c.parent = a.name and c.depreciation_amount > 0)
												))
											and a.docstatus = 1
											and (
												a.status not in ('Scrapped', 'Sold')
												OR
												(a.status in ('Scrapped', 'Sold') AND a.disposal_date >= '{1}' and b.schedule_date <= a.disposal_date)
											)
								 			and b.depreciation_amount > 0
								 	) as result
									""".format(a.name, filters.from_date), as_dict=True)
		
		opening_it_dep_zero = frappe.db.sql("""select 
												sum(a.opening_accumulated_depreciation) as it_opening
							   			from `tabAsset` a, `tabDepreciation Schedule` b
						 	 			where a.name = b.parent
						  					and a.asset_category = '{0}'
						  					and '{1}' between b.schedule_start_date and b.schedule_date
											and a.docstatus = 1
								 			and b.depreciation_amount <= 0
											and not exists(
													select 1 from `tabDepreciation Schedule` c where c.parent=a.name and c.schedule_date < '{1}' and c.depreciation_amount > 0
												)
											and (
												a.status not in ('Scrapped', 'Sold')
												OR
												(a.status in ('Scrapped', 'Sold') AND a.disposal_date >= '{1}')
											)
									""".format(a.name, filters.from_date), as_dict=True)

		opening_dep = frappe.db.sql("""select  sum(a.opening_accumulated_depreciation) as it_opening
										from `tabAsset` a
						 	 			where a.asset_category = '{0}'
						  					and a.docstatus = 1
											and (
												a.status not in ('Scrapped', 'Sold')
												OR
												(a.status in ('Scrapped', 'Sold') AND a.disposal_date >= '{1}')
											)
											and NOT EXISTS(
												select 1
												from  `tabDepreciation Schedule` b
												where b.parent = a.name
											)	
								""".format(a.name, filters.from_date), as_dict=True)
		eliminated_dep = frappe.db.sql(
								"""
								SELECT 
									sum(results.depreciation_eliminated_during_the_period) as depreciation_eliminated_during_the_period
								from (SELECT 
										ifnull(sum(case when ifnull(a.disposal_date, 0) != 0 and a.disposal_date >= %(from_date)s
																and a.disposal_date <= %(to_date)s and ds.schedule_date <= a.disposal_date then
														ROUND(ds.depreciation_amount, 2)
													else
														0
													end), 0) as depreciation_eliminated_during_the_period
									from `tabAsset` a, `tabDepreciation Schedule` ds
									where a.docstatus=1 and a.company=%(company)s and a.purchase_date <= %(to_date)s and a.name = ds.parent
										and a.asset_category=%(asset_category)s
									union
									SELECT 
										ifnull(sum(case when a.disposal_date >= %(from_date)s and a.disposal_date <= %(to_date)s then
														ROUND(a.opening_accumulated_depreciation, 2)
													else
														0
													end), 0) as depreciation_eliminated_during_the_period
									from `tabAsset` a
									where a.docstatus=1 and a.company=%(company)s and a.purchase_date <= %(to_date)s
										and a.asset_category=%(asset_category)s) as results
								""",
								{"to_date": filters.to_date, "from_date": filters.from_date, "company": filters.company, "asset_category": a.name},
								as_dict=1,
							)
		
		acc_it_zero = opening_it_dep_zero[0].it_opening if opening_it_dep_zero[0].it_opening else 0.00
		acc_it = opening_it_dep[0].acc_income_tax if opening_it_dep[0].acc_income_tax else 0.00
		depreciation_it = opening_it_dep[0].depreciation_income_tax if opening_it_dep[0].depreciation_income_tax else 0.00
		it_opening = opening_dep[0].it_opening if opening_dep[0].it_opening else 0.00
		
		row = [ 
			
		]	
		data.append({
			"asset_category": a.name,
			"gross_opening":g_open,
			"gross_addition":g_addition,
			"gross_adjustment":g_adjustment,
			"gross_total":g_total,
			"dep_opening":d_open,
			"dep_addition":dep_addition,
			"dep_adjustment":dep_adjust,
			#adj_adjust,
			"dep_total":d_total,
			"net_block":flt(g_total) - flt(d_total),
			"opening_income_tax":acc_it - depreciation_it + it_opening + acc_it_zero,
			"it_dep_addition":income_tax[0].total_income_tax,
			"it_dep_eliminated":eliminated_dep[0].depreciation_eliminated_during_the_period
		})

	#For CWIP Account
	if flt(filters.include_cwip):
		row = get_cwip(filters)
		data.append(row)
	return data

def get_cwip(filters):
	cwip_acc = []
	cwip_account = frappe.db.get_value("Company", filters.get("company"), "capital_work_in_progress_account")
	if not cwip_account:
		frappe.throw("Capital Work In Progress Account is missing. Please set CWIP account in Company Setting")
	cwip_accounts_gl = frappe.db.sql("select name from tabAccount where parent_account = %s", cwip_account, as_dict=True)
	for account in cwip_accounts_gl:
		cwip_acc.append(str(account.name))
	cwip_accounts = tuple(cwip_acc)

	cwip_open = get_values(cwip_accounts, filters.to_date, filters.from_date, filters.cost_center, opening=True, cwip=True)
	cwip = get_values(cwip_accounts, filters.to_date, filters.from_date, filters.cost_center, cwip=True)

	cwip_open = cwip_open[0]
	cwip = cwip[0]

	c_open = flt(cwip_open.debit) - flt(cwip_open.credit)
	c_total = c_open + flt(cwip.debit) - flt(cwip.credit)

	# row = [
	# 	"Capital Work in Progress",
	# 	c_open,
	# 	cwip.debit,
	# 	cwip.credit,
	# 	c_total,
	# 	0,
	# 	0,
	# 	0,
	# 	0,
	# 	0,
	# 	c_total 
	# ]	
	row = dict()
	row.update({
			"asset_category": "Capital Work in Progress",
			"gross_opening":c_open,
			"gross_addition":cwip.debit,
			"gross_adjustment":cwip.credit,
			"gross_total":c_total,
			"dep_opening":0,
			"dep_addition":0,
			"dep_adjustment":0,
			#adj_adjust,
			"dep_total":0,
			"net_block":0,
			"opening_income_tax":c_total,
			"it_dep_addition":0
		})
	return row

def get_values(account, to_date, from_date, cost_center=None, opening=False, cwip=False, adjustment=False):
#	query = "select sum(debit) as debit, sum(credit) as credit from `tabGL Entry` where account = \'" + str(account) + "\' and docstatus = 1"
	if cwip:
		query = "select sum(debit) as debit, sum(credit) as credit from `tabGL Entry` where account in " + str(account) + " and docstatus = 1 and is_cancelled = 0"
	elif adjustment:
		return [frappe._dict({"debit": 0.0, "credit": 0.0})]
		#query = "select sum(debit) as debit, sum(credit) as credit from `tabGL Entry` where account = \'" + str(account) + "\' and docstatus = 1 and is_depreciation_adjustment = 'Yes'"
	else:
		query = "select sum(debit) as debit, sum(credit) as credit from `tabGL Entry` where account = \'" + str(account) + "\' and docstatus = 1 and is_cancelled = 0"
	if not opening:
		query += " and posting_date between \'" + str(from_date) + "\' and \'" + str(to_date) + "\'"
	else:
		query += " and posting_date < \'" + str(from_date) + "\'"
	if cost_center:
		query += " and cost_center = \'" + str(cost_center) + "\'"

	query += " and voucher_type not in ('Period Closing Voucher', 'Asset Movement', 'Bulk Asset Transfer')"
	query += " and voucher_no not in ( select name from `tabJournal Entry` where docstatus=1 and reverse_jv = 1 )"
	#query += " and voucher_type not in ('Period Closing Voucher')"
	#if account == "Machinery & Equipment(10 Years) - CDCL":
	#	frappe.msgprint(" Query : {}".format(query))
	value = frappe.db.sql(query, as_dict=True)

	return value


def get_columns():
	return [
		{
			"fieldname": "asset_category",
			"label": _("Asset Category"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "gross_opening",
			"label": _("Opening Acquisation"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "gross_addition",
			"label": _("Acquisation During the Year"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "gross_adjustment",
			"label": _("Adjustment During the Year"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "gross_total",
			"label": _("Gross Total"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "dep_opening",
			"label": _("Open IT Dep."),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "dep_addition",
			"label": _("IT Dep. During the Year"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "dep_adjustment",
			"label": _("Dep. Adjustment During the Year"),
			"fieldtype": "Currency",
			"width": 150
		},
		#{
				#        "fieldname": "adjustment",
				#        "label": _("Adjustment"),
				#        "fieldtype": "Currency",
				#        "width": 150
				#},
		{
			"fieldname": "dep_total",
			"label": _("Dep. Total"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "net_block",
			"label": _("Net Block"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "opening_income_tax",
			"label": _("Accumulated Dep."),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "it_dep_addition",
			"label": _("Dep. During the Year"),
			"fieldtype": "Currency",
			"width": 150
		},
		{
			"fieldname": "it_dep_eliminated",
			"label": _("Dep. Eliminated During the Year"),
			"fieldtype": "Currency",
			"width": 150
		},
]

#
# BACKUPS
#

# backup by SHIV on 2021/03/2021 
def get_accounts_bkp20210310(filters):
	data = []
	for a in frappe.db.sql("SELECT a.name, b.fixed_asset_account as fa, b.accumulated_depreciation_account as acc, b.depreciation_expense_account as dep from `tabAsset Category` a, `tabAsset Category Account` b where a.name = b.parent", as_dict=True):
		gross_opening = get_values(a.fa, filters.to_date, filters.from_date, filters.cost_center, opening=True)[0]
		gross = get_values(a.fa, filters.to_date, filters.from_date, filters.cost_center)[0]
		dep_opening = get_values(a.acc, filters.to_date, filters.from_date, filters.cost_center, opening=True)[0]
		acc_dep = get_values(a.acc, filters.to_date, filters.from_date, filters.cost_center)[0]
		dep = get_values(a.dep, filters.to_date, filters.from_date, filters.cost_center)[0]
		adj = get_values(a.acc, filters.to_date, filters.from_date, filters.cost_center, adjustment=True)[0]		

		g_open = flt(gross_opening.debit) - flt(gross_opening.credit)
		g_addition = flt(gross.debit)
		g_adjustment = flt(gross.credit)
		g_total = g_open + g_addition - g_adjustment 
		d_open = -1 * (flt(dep_opening.debit) - flt(dep_opening.credit))
		dep_adjust = flt(acc_dep.debit)
		adj_adjust = flt(adj.credit)
		dep_addition = flt(acc_dep.credit) - flt(adj.credit)
		dep_add = flt(acc_dep.credit)
		d_total = d_open + dep_add  - flt(dep_adjust)

		row = [ 
			a.name,
			g_open,
			g_addition,
			g_adjustment,
			g_total,
			d_open,
			dep_addition,
			dep_adjust,
			#adj_adjust,
			d_total,
			flt(g_total) - flt(d_total) 
		]	
		data.append(row)

	#FOr CWIP Account
	cwip_acc = []
	cwip_account = frappe.db.get_single_value("Accounts Settings", "cwip_account")
	cwip_accounts_gl = frappe.db.sql("select name from tabAccount where parent_account = %s", cwip_account, as_dict=True)
	for account in cwip_accounts_gl:
		cwip_acc.append(str(account.name))
	cwip_accounts = tuple(cwip_acc)

	cwip_open = get_values(cwip_accounts, filters.to_date, filters.from_date, filters.cost_center, opening=True, cwip=True)
	cwip = get_values(cwip_accounts, filters.to_date, filters.from_date, filters.cost_center, cwip=True)

	cwip_open = cwip_open[0]
	cwip = cwip[0]

	c_open = flt(cwip_open.debit) - flt(cwip_open.credit)
	c_total = c_open + flt(cwip.debit) - flt(cwip.credit)

	row = [
		"Capital Work in Progress",
		c_open,
		cwip.debit,
		cwip.credit,
		c_total,
		0,
		0,
		0,
		0,
		0,
		c_total 
	]	
	data.append(row)
	return data

