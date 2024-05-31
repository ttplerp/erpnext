# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.custom_utils import test,update_gross_sal,update_ranking,update_builCate,update_ranking_3pa,updateNotEligibleRanking
class RentalSetting(Document):
	pass



@frappe.whitelist()
def updateHousingApplicants(user):
    # Your logic to update salaries and rank goes here
    
    test()
    update_gross_sal()
    update_ranking()
    update_builCate()
    update_ranking_3pa()
    updateNotEligibleRanking()
    # frappe.throw(user)