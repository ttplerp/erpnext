# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_data(filters=None):
	data=[]
	condition=""
	if filters.from_date and filters.to_date:
		condition += """ and tm.training_start_date between "{}" and "{}" """.format(filters.from_date, filters.to_date)
	if filters.domain:
		condition += """ and tm.domain="{}" """.format(filters.domain)
	if filters.programme:
		condition += """ and tm.programme="{}" """.format(filters.programme)
	if filters.did:
		condition += """ and td.desuup_id="{}" """.format(filters.did)

	for a in frappe.db.sql("""select count(td.desuup_id) as count, td.desuup_id, 
				td.desuup_name, td.desuup_cid, td.gender
				from `tabTraining Management` tm inner join `tabTrainee Details` td 
				on tm.name=td.parent
				where tm.docstatus!=2
				{}
				group by td.desuup_id
				order by count desc
			""".format(condition),as_dict=True):
		reference = ""
		for b in frappe.db.sql(""" select tm.name, tm.programme, tm.domain, tm.training_start_date
					from `tabTraining Management` tm inner join `tabTrainee Details` td 
					on tm.name=td.parent
					where tm.docstatus!=2
					and td.desuup_id='{}'
					order by tm.training_start_date
				""".format(a.desuup_id), as_dict=True):
			reference += str(b.name) + ", "
		row={ "did": a.desuup_id, "name":a.desuup_name, "cid":a.desuup_cid, "gender":a.gender, "dsp_attended":a.count, "reference":reference}
		data.append(row)
	return data

def get_columns(filters):
	columns = [
			 _("DID") + ":Link/Desuup:150", 
			 _("Name") + ":Data:170",
			 _("CID") + ":Data:130",
			 _("Gender") + ":Data:100",
			 _("DSP Attended") + ":Data:120",
			 _("Reference") + ":Data:800",
	]
	return columns