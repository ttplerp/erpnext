from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
        'fieldname': 'execute_audit_no',
		'transactions': [
			{
				'label': _('Related'),
				'items': ['Audit Initial Report','Follow Up', 'Close Follow Up']
			},
		]
	}
