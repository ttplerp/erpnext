# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, rounded, cint,getdate, nowdate
from erpnext.custom_utils import get_production_groups
from erpnext.accounts.report.financial_statements import get_columns,get_period_list

def execute(filters=None):
	data = []
	period_list = get_period_list(
					from_fiscal_year    = filters.fiscal_year,
					to_fiscal_year      = filters.fiscal_year,
					period_start_date   = getdate(str(filters.fiscal_year + '-01-01')),
					period_end_date     = getdate(str(filters.fiscal_year + '-12-31')),
					filter_based_on     = filters.filter_based_on,
					periodicity         = filters.periodicity,
					company             = filters.company)
	columns = get_columns(filters, period_list)
	data 	= get_data(filters, period_list)
	# chart removed as it not required by cilent
	# chart 	= get_chart_data(filters, columns,data,period_list)
	return columns, data

def get_chart_data(filters, columns, data, period_list):
	labels = []
	values = []
	for d in data:
		if d.get("particulars") == filters.chart_base_on:
			for p in period_list:
				values.append(flt(d[str(p.key)],2))
				labels.append(p.label)
	chart = {"data": {"labels": labels, 
			"datasets":[{"name": _(filters.chart_base_on), "values": values}]},
			"type":"bar",
			"height": 150,
			"barOptions": { "spaceRatio": 0.1}
			}
	return chart
def get_data(filters, period_list): 
	data = []
	items = get_items(filters)
	if not items:
		frappe.throw("No Sales Target found for {} in Fiscal Year {}".format(frappe.bold(filters.item_sub_group),frappe.bold(filters.fiscal_year)))

	item_cond = " AND si.item_code {}".format("IN {}".format(tuple(items)) if len(items) > 1 else "= '{}'".format(items[0])) 

	target_qty_row = frappe._dict({
		"particulars":"Total Target Qty(MT)", "total":0
	})
	adjusted_qty_row = frappe._dict({
		"particulars":"Adjusted Qty(MT)", "total":0
	})
	achieved_qty_row = frappe._dict({
		"particulars":"Achieved Qty (MT)","total":0
	})
	progress = frappe._dict({
		"particulars":"Progress(%)","total":0
	})
	cumulative_sale_row=frappe._dict({
		"particulars":"Cumulative (Sales)", "total":0
	})
	cumulative_progress_row=frappe._dict({
		"particulars":"Cumulative Sales Progress(%)", "total":0
	})
	# frappe.throw(str(period_list))
	for p in period_list:
		# get targeted qty
		target_qty = frappe.db.sql('''
			SELECT SUM(IFNULL(si.total_target_qty,0)), s.total_target_qty,SUM(IFNULL(si.adjusted_qty,0)), s.total_adjusted_qty FROM `tabSales Target` s INNER JOIN `tabSales Target Item` si
			ON si.parent = s.name
			WHERE s.item_sub_group = '{item_sub_group}' AND s.fiscal_year = '{fiscal_year}' 
			AND si.from_date >= '{from_date}' AND si.to_date <= '{to_date}' AND s.docstatus = 1
			'''.format(item_sub_group = filters.item_sub_group, fiscal_year = filters.fiscal_year, from_date = p.from_date, to_date=p.to_date ))
		
		if target_qty[0][0]:
			target_qty_row[str(p.key)] = flt(target_qty[0][0],2)
			target_qty_row["total"] = flt(target_qty[0][1],2)
			adjusted_qty_row[str(p.key)] = flt(target_qty[0][2],2)
			adjusted_qty_row["total"] = flt(target_qty[0][3],2)
		else:
			target_qty_row[str(p.key)] = 0
			adjusted_qty_row[str(p.key)] = 0


		# get achieved qty
		achieved_qty = frappe.db.sql('''
			SELECT SUM(si.accepted_qty) FROM `tabSales Invoice` s INNER JOIN `tabSales Invoice Item` si ON s.name = si.parent
			WHERE posting_date BETWEEN '{from_date}' AND '{to_date}'
			AND s.docstatus = 1 AND s.is_return = 0
			{item_cond}
		'''.format(from_date = p.from_date, to_date=p.to_date, item_cond = item_cond))
			
		if achieved_qty[0][0]:
			# acieved qty
			achieved_qty_row[str(p.key)] = flt(achieved_qty[0][0],2)
			achieved_qty_row["total"] += flt(achieved_qty_row[str(p.key)],2)

			# calculate cumulative sale 
			cumulative_sale_row[str(p.key)] = flt(achieved_qty_row["total"],2)
			cumulative_sale_row['total'] = flt(cumulative_sale_row[str(p.key)],2)

			# calculate cumulative progress 
			cumulative_progress_row[str(p.key)] = flt(flt(cumulative_sale_row[str(p.key)]) / flt(target_qty_row["total"]) * 100,2)
			cumulative_progress_row["total"] += flt(cumulative_progress_row[str(p.key)],2)
		else:
			achieved_qty_row[str(p.key)] = 0
			cumulative_sale_row[str(p.key)] = flt(cumulative_sale_row["total"],2)
			cumulative_progress_row[str(p.key)] = 0

		# calculate progress
		if target_qty[0][0]:
			progress[str(p.key)] = flt(flt(achieved_qty_row[str(p.key)])/flt(target_qty[0][0]) * 100,2)
			progress["total"] += flt(progress[str(p.key)],2)
		else:
			progress[str(p.key)] = 0

	data.append(target_qty_row)
	data.append(adjusted_qty_row)
	data.append(achieved_qty_row)
	data.append(progress)
	data.append(cumulative_sale_row)
	data.append(cumulative_progress_row)

	return data
def get_items(filters):
	return [ i.item_code for i in frappe.db.sql('''select s.item_code
						from `tabSales Target` t inner join `tabSubgroup Item` s 
						on t.name = s.parent  
						where t.item_sub_group = '{}' 
						and t.fiscal_year = '{}' 
						and t.docstatus=1'''.format(filters.item_sub_group,filters.fiscal_year), as_dict=True)]
def get_columns(filters , period_list):
	columns = [
		{
			"fieldname": "particulars",
			"label": _("{}".format(filters.item_sub_group)),
			"fieldtype": "Data",
			"width": 230
		}
	]

	for period in period_list:
		columns.append({
			"fieldname": period.key,
			"label": period.label,
			"fieldtype": "Float",
			"width": 130,
			"precision":2
		})
	columns.append({
			"fieldname": "total",
			"label": "Total",
			"fieldtype": "Float",
			"width": 100,
			"precision":2
		})
	return columns