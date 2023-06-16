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
	condition=""
	if filters.from_date and filters.to_date:
		condition += """ and tm.training_start_date between "{}" and "{}" """.format(filters.from_date, filters.to_date)
	if filters.domain:
		condition += """ and tm.domain="{}" """.format(filters.domain)
	if filters.programme:
		condition += """ and tm.programme="{}" """.format(filters.programme)
	if filters.did:
		condition += """ and td.desuup_id="{}" """.format(filters.did)
	
	if filters.detail:
		query="""
				select td.desuup_id, 
				td.desuup_name, td.desuup_cid, td.gender, tm.domain, 
				tm.programme, tm.training_center,
				tm.training_start_date, tm.training_end_date, tm.name
				from `tabTraining Management` tm inner join `tabTrainee Details` td 
				on tm.name=td.parent
				where tm.docstatus!=2
				and td.status not in ("Withdrawn","Terminated","Suspended")
				{}
				order by td.desuup_id
			 """.format(condition)
	else:
		query="""select td.desuup_id, 
				td.desuup_name, td.desuup_cid, td.gender, count(td.desuup_id) as count
				from `tabTraining Management` tm inner join `tabTrainee Details` td 
				on tm.name=td.parent
				where tm.docstatus!=2
				and td.status not in ("Withdrawn","Terminated","Suspended")
				{}
				group by td.desuup_id
				order by count desc
			""".format(condition)
	return frappe.db.sql(query)

def get_columns(filters):
	columns = [
			 _("Desuup ID") + ":Link/Desuup:150", 
			 _("Name") + ":Data:170",
			 _("Desuup CID") + ":Data:130",
			 _("Gender") + ":Data:100",
	]
	if filters.detail:
		columns += [
			_("Domain") + ":Link/DSP Domain:150", 
			_("Programme") + ":Link/Programme:170",
			_("Training Center") + ":Link/Training Center:160",
			_("Start Date") + ":Date:100",
			_("End Date") + ":Date:100",
			_("Reference") + ":Link/Training Management:100",
		]
	if not filters.detail:
		columns += [
			 _("Programme Attended") + ":Data:120",
		]
	return columns