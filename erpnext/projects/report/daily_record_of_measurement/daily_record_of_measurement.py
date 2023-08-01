# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		("BOQ Item") + "::120",
		("Item Description") + "::250",
		("Posting Date") + ":Date:100",
		("Location") + "::120",
		("No") + "::120",
		("Length (m)") + "::120",
		("Breadth (m)") + "::120",
		("Height (m)")+ "::150",
		("Quantity") + ":Float:150",
		("UOM") + ":Link/UOM:150",
		("Rate (Nu.)") + ":Float:120",
		("Amount (Nu.)") + ":Float:120",
		("Remarks") + "::120",

	]

def get_data(filters):
	cond = ""
	data = []
	rom_data = {}
	if filters.from_date:
		cond += " and rom.posting_date >= '{}'".format(filters.get("from_date"))
	if filters.to_date:
		cond += " and rom.posting_date <= '{}'".format(filters.get("to_date"))
	if filters.project:
		cond += " and rom.project = '{}'".format(filters.get("project"))
	rom = frappe.db.sql("""
		select rom.posting_date,
		rom.boq_code,
		rom.item_name,
		romi.location,
		romi.no,
		romi.length,
		romi.breadth,
		romi.height,
		romi.quantity,
		rom.uom,
		rom.rate,
		romi.amount,
		rom.remarks
		from `tabRecord Of Measurement` rom,
		`tabRecord Of Measurement Item` romi
		where romi.parent = rom.name
		and rom.docstatus = 1
		{}
		order by rom.boq_code, rom.posting_date
	""".format(cond),as_dict=1)
	if rom:
		for a in rom:
			if a.boq_code not in rom_data:
				rom_data.update({
					a.boq_code:[{
						"description": a.item_name,
						"location": a.location,
						"posting_date": a.posting_date,
						"no": a.no,
						"length": a.length,
						"breadth": a.breadth,
						"height": a.height,
						"quantity":a.quantity,
						"uom": a.uom,
						"rate": a.rate,
						"amount": a.amount,
						"remarks": a.remarks
					}]})
			else:
				rom_data[a.boq_code].append({
						"description": a.item_name,
						"location": a.location,
						"posting_date": a.posting_date,
						"no": a.no,
						"length": a.length,
						"breadth": a.breadth,
						"height": a.height,
						"quantity":a.quantity,
						"uom": a.uom,
						"rate": a.rate,
						"amount": a.amount,
						"remarks": a.remarks
				})
	total_amount = total_quantity = 0
	for b in rom_data:
		data.append([b,rom_data[b][0]['description'],None,None,None,None,None,None,None,rom_data[b][0]['uom'],None,None,None])
		sub_total_qty = sub_total_amount = rate = 0
		for c in rom_data[b]:
			data.append([
				None,
				None,
				c['posting_date'],
				c['location'],
				c['no'],
				c['length'],
				c['breadth'],
				c['height'],
				c['quantity'],
				None,
				c['rate'],
				c['amount'],
				c['remarks']
			])
			sub_total_qty += flt(c['quantity'],2)
			total_quantity += flt(c['quantity'],2)
			sub_total_amount += flt(c['amount'],2)
			total_amount += flt(c['amount'],2)
			rate = c['rate']
		data.append([None,"Cumulative Total for P/L PCC 1:3:6 in foundation",None,None,None,None,None,None,sub_total_qty,None,rate,sub_total_amount,None])
	data.append([None,"Total work done Amount of the day (Income) -(Nu):",None,None,None,None,None,None,total_quantity,None,None,total_amount,None])

	return data

