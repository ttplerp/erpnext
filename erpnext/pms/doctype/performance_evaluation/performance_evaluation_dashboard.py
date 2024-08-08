from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
	'fieldname': 'name',
		'non_standard_fieldnames': {
			'PMS Appeal': 'appeal_based_on',
		},
		'transactions': [
			{
				'label': _('PMS Appeal'),
				'items': ['PMS Appeal']
			}
		]
	}
