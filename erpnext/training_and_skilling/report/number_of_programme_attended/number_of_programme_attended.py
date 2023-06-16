# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters):
	data=[]
	for a in frappe.db.sql("""select
								CASE
									WHEN a.dsp_attended = 1 THEN 'Single Programme'
									WHEN a.dsp_attended = 2 THEN 'Two Programme'
									WHEN a.dsp_attended = 3 THEN 'Three Programme'
									WHEN a.dsp_attended = 4 THEN 'Four Programme'
									WHEN a.dsp_attended = 5 THEN 'Five Programme'
									WHEN a.dsp_attended = 6 THEN 'Six Programme'
									WHEN a.dsp_attended = 7 THEN 'Seven Programme'
									WHEN a.dsp_attended = 8 THEN 'Eight Programme'
									WHEN a.dsp_attended = 9 THEN 'Nine Programme'
									WHEN a.dsp_attended = 10 THEN 'Ten Programme'
									ELSE 'More Than Ten Programme'
								END as programmes,
								count(a.dsp_attended) as total
								from
									(select count(td.desuup_id) as dsp_attended, td.desuup_id, 
									td.desuup_name, td.desuup_cid, td.gender
									from `tabTraining Management` tm inner join `tabTrainee Details` td 
									on tm.name=td.parent
									where tm.docstatus!=2
									and td.status not in ("Withdrawn","Terminated","Suspended")
									group by td.desuup_id) a
								group by a.dsp_attended
			""", as_dict=True):
		row={"programmes":a.programmes, "total":a.total}
		data.append(row)
	return data

def get_columns(filters):
	columns = [
		{
			"label": _("Number of Programme"),
			"fieldtype": "Data",
			"fieldname": "programmes",
			"width": 180,
		},
		{
			"label": _("Total De-Suups"),
			"fieldname": "total",
			"fieldtype": "Data",
			"width": 180,
		},
	]
	return columns

