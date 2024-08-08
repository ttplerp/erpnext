from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'name',
		'non_standard_fieldnames': {
			'Review': 'target',
		},
		'transactions': [
			{
				'label': _('Review'),
				'items': ['Review']
			}
		]
	}
