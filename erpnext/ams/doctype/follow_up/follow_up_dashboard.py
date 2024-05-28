from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
        'fieldname': 'follow_up_no',
		'transactions': [
			{
				'label': _('Related'),
				'items': ['Close Follow Up']
			},
		]
	}
