# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from dateutil.relativedelta import relativedelta

import frappe
from frappe import _
from frappe.utils import getdate
from frappe.utils.dashboard import cache_source


@frappe.whitelist()
@cache_source
def get_data(
	chart_name=None,
	chart=None,
	no_cache=None,
	filters=None,
	from_date=None,
	to_date=None,
	timespan=None,
	time_interval=None,
	heatmap_year=None,
) -> dict[str, list]:

	completed_training = frappe.db.sql('''
        select domain, count(name) as tot_count from `tabTraining Management` where docstatus = 1 group by domain
    ''', as_dict=True)

	labels , values = [], []
	for l in completed_training:
		labels.append(f'{l.domain}')
		values.append(l.tot_count)
	return {
		"labels": labels,
		"datasets": [
			{"name": _("Training Completed"), "values": values},
		],
	}

