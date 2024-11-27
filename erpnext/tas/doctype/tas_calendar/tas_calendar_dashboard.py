from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'name',
        'non_standard_fieldnames': {
			'TAS Extension': 'tas_calendar',
        },
		'transactions': [
			{
				'label': _('Extension'),
				'items': ['TAS Extension']
			}
        ]
	}