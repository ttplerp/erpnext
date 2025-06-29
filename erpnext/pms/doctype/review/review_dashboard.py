from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
	'fieldname': 'name',
		'non_standard_fieldnames': {
			'Performance Evaluation': 'review',
		},
		'transactions': [
			{
				'label': _('Performance Evaluation'),
				'items': ['Performance Evaluation']
			}
		]
	}
