from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
        'fieldname': 'audit_engagement_letter',
		'transactions': [
			{
				'label': _('Related'),
				'items': ['Prepare Audit Plan', 'Execute Audit', 'Audit Initial Report', 'Follow Up', 'Close Follow Up']
			},
		]
	}
