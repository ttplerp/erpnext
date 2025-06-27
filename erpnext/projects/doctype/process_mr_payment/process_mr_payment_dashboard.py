from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		# 'heatmap': True,
		# 'heatmap_message': _('PMS Calendar Extension Record'),
		'fieldname': 'reference_name',
        # "non_standard_fieldnames": {"Project Payment": "reference_name"},
		'transactions': [
			{
				'label': _('Related'),
				'items': ['Journal Entry']
			}
        ]
	}