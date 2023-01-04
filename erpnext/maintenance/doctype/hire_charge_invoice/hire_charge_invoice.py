# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cstr, flt, fmt_money, formatdate, nowdate
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.custom_utils import check_uncancelled_linked_doc, check_future_date, check_budget_available
from erpnext.maintenance.maintenance_utils import get_equipment_ba
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from frappe import _

class HireChargeInvoice(AccountsController):
    def validate(self):
        check_future_date(self.posting_date)
        self.check_advances(self.ehf_name)
        self.set_advance_data()
        self.set_discount_data()
        self.set_amount()
        if self.total_invoice_amount <= 0:
            frappe.throw("Total Invoice Amount should be greater than 0")
        if self.balance_amount < 0:
            frappe.throw("Balance amount cannot be negative")
        if self.owned_by != "Own Company":
            hire_expense_account = frappe.db.get_single_value("Maintenance Accounts Settings", "hire_expense_account")
            check_budget_available(self.cost_center,hire_expense_account,self.posting_date,self.total_invoice_amount,self.business_activity)

    def set_advance_data(self):
        advance_amount = 0
        balance_amount = 0
        for a in self.advances:
            a.balance_advance_amount = flt(a.actual_advance_amount) - flt(a.allocated_amount)
            if flt(a.balance_advance_amount) < 0:
                frappe.throw("Allocated Amount should be smaller than Advance Available")
            advance_amount = flt(advance_amount) + flt(a.allocated_amount)
            balance_amount = flt(balance_amount) + flt(a.balance_advance_amount)
        self.advance_amount = advance_amount
        self.balance_advance_amount = balance_amount

    def set_discount_data(self):
        discount_amount = 0
        total_amount = 0
        for a in self.items:
            if flt(a.discount_amount) < 0 or flt(a.discount_amount) > flt(a.total_amount):
                frappe.throw("Discount Amount should be smaller than Total Aamount")
            discount_amount = flt(discount_amount) + flt(a.discount_amount)
            total_amount = flt(total_amount) + flt(a.total_amount)
        self.discount_amount = discount_amount
        self.total_invoice_amount = total_amount

    def set_amount(self):
        self.balance_amount = flt(self.total_invoice_amount) - flt(self.advance_amount) - flt(self.discount_amount) - flt(self.tds_amount)
        self.outstanding_amount = self.balance_amount

    def on_submit(self):
        self.check_vlogs()
        self.set_advance_data()
        self.update_advance_amount();
        self.update_vlogs(1)
        if self.owned_by == "Own Company":
            self.post_journal_entry()
            self.db_set("outstanding_amount", 0)
        else:
            hire_expense_account = frappe.db.get_single_value("Maintenance Accounts Settings", "hire_expense_account")
            check_budget_available(self.cost_center,hire_expense_account,self.posting_date,self.total_invoice_amount,self.business_activity)
            self.commit_budget(hire_expense_account)
            self.consume_budget(hire_expense_account)
            self.make_gl_entries()

        if self.close:
            self.refund_of_excess_advance()
        self.check_close()

    def on_cancel(self):
        if self.owned_by != "Own Company":
            self.make_gl_entries()
            self.cancel_budget_entry()

            #self.make_gl_entries_on_cancel()
        check_uncancelled_linked_doc(self.doctype, self.name)
        cl_status = frappe.db.get_value("Journal Entry", self.invoice_jv, "docstatus")
        if cl_status and cl_status != 2:
            frappe.throw("You need to cancel the journal entry ("+ str(self.invoice_jv) + ")related to this invoice first!")
        if self.payment_jv:
            cl_status = frappe.db.get_value("Journal Entry", self.payment_jv, "docstatus")
            if cl_status and cl_status != 2:
                frappe.throw("You need to cancel the journal entry ("+ str(self.payment_jv) + ")related to this invoice first!")
        self.readjust_advance()
        if self.close:
            self.check_advances()
        self.update_vlogs(0)
        self.check_close(1)
        self.db_set("invoice_jv", "")
        self.db_set("payment_jv", "")

    def check_advances(self, cancel=None):
        hire_name = self.ehf_name
        if cancel:
            hire_name = self.name
        advance = frappe.db.sql("select t1.name from `tabJournal Entry` t1, `tabJournal Entry Account` t2 where t1.name = t2.parent and t2.is_advance = 'Yes' and (t1.docstatus = 1 or t1.docstatus = 0) and t2.reference_name = \'" + str(hire_name)  + "\'", as_dict=True)
        if advance and not cancel and not self.advances:
            frappe.msgprint("There is a Advance Payment for this Hire Form. You might want to pull it using 'Get Advances' button")
        if advance and cancel:
            frappe.throw("Cancel the Refund Journal Entry " + str(advance[0].name) + " before cancelling")

    def update_advance_amount(self):
        lst = []
        for d in self.get('advances'):
            if flt(d.allocated_amount) > 0:
                args = frappe._dict({
                    'voucher_type': 'Journal Entry',
                    'voucher_no' : d.jv_name,
                    'voucher_detail_no' : d.reference_row,
                    'against_voucher_type' : self.doctype,
                    'against_voucher'  : self.name,
                    'account' : d.advance_account,
                    'party_type': "Supplier",
                    'party': self.customer,
                    'is_advance' : 'Yes',
                    'dr_or_cr' : "credit_in_account_currency",
                    'unadjusted_amount' : flt(d.actual_advance_amount),
                    'allocated_amount' : flt(d.allocated_amount),
                    'exchange_rate': 1,
                    'business_activity': get_default_ba()
                })
                lst.append(args)

        if lst:
            from erpnext.accounts.utils import reconcile_against_document
            reconcile_against_document(lst)


    def check_vlogs(self):
        for a in self.items:
            ic = frappe.db.get_value("Vehicle Logbook", a.vehicle_logbook, "invoice_created")			
            if ic:
                frappe.throw("Logbook <b>" + str(a.vehicle_logbook) + "</b> has already been invoiced")

    def update_vlogs(self, value):
        for a in self.items:
            logbook = frappe.get_doc("Vehicle Logbook", a.vehicle_logbook)			
            logbook.db_set("invoice_created", value)

    ##
    # make necessary journal entry
    ##
    def post_journal_entry(self):
        receivable_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_receivable_account")
        if not receivable_account:
            frappe.throw("Setup Reveivable Account in Maintenance Accounts Settings")
        advance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_advance_account")
        if not advance_account:
            frappe.throw("Setup Advance Account in Maintenance Accounts Settings")
        hire_account = frappe.db.get_single_value("Maintenance Accounts Settings", "hire_revenue_account")
        if not hire_account:
            frappe.throw("Setup Hire Account in Maintenance Accounts Settings")
        hr_account = frappe.db.get_single_value("Maintenance Accounts Settings", "hire_revenue_internal_account")
        if not hr_account:
            frappe.throw("Setup Hire Revenue Internal Account in Maintenance Accounts Settings")
        hea_account = frappe.db.get_single_value("Maintenance Accounts Settings", "hire_expense_account")
        if not hea_account:
            frappe.throw("Setup Hire Expense Internal Account in Maintenance Accounts Settings")
        discount_account = frappe.db.get_single_value("Maintenance Accounts Settings", "discount_account")
        if not discount_account:
            frappe.throw("Setup Discount Account in Maintenance Accounts Settings")

        default_ba = get_default_ba()

        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1 
        je.title = "Hire Charge Invoice (" + self.name + ")"
        je.voucher_type = 'Hire Invoice'
        je.naming_series = 'Hire Invoice'
        je.remark = 'Payment against : ' + self.name;
        je.posting_date = self.posting_date
        je.branch = self.branch

        if self.owned_by == "Own Company":
            customer_cost_center = frappe.db.get_value("Equipment Hiring Form", self.ehf_name, "customer_cost_center")
            for a in self.items:
                equip_ba = get_equipment_ba(a.equipment)
                je.append("accounts", {
                        "account": hea_account,
                        "reference_type": "Hire Charge Invoice",
                        "reference_name": self.name,
                        "cost_center": customer_cost_center,
                        "debit_in_account_currency": flt(a.total_amount),
                        "debit": flt(a.total_amount),
                        "business_activity": equip_ba
                    })
                je.append("accounts", {
                        "account": hr_account,
                        "reference_type": "Hire Charge Invoice",
                        "reference_name": self.name,
                        "cost_center": self.cost_center,
                        "credit_in_account_currency": flt(a.total_amount),
                        "credit": flt(a.total_amount),
                        "business_activity": equip_ba
                    })
            
            allow_inter_company_transaction = frappe.db.get_single_value("Accounts Settings", "auto_accounting_for_inter_company")
            if allow_inter_company_transaction:
                ic_account = frappe.db.get_single_value("Accounts Settings", "intra_company_account")
                if not ic_account:
                    frappe.throw("Setup Intra-Company Account in Accounts Settings")
                je.append("accounts", {
                        "account": ic_account,
                        "reference_type": "Hire Charge Invoice",
                        "reference_name": self.name,
                        "cost_center": customer_cost_center,
                        "credit_in_account_currency": flt(self.total_invoice_amount),
                        "credit": flt(self.total_invoice_amount),
                        "business_activity": default_ba
                    })
                je.append("accounts", {
                        "account": ic_account,
                        "reference_type": "Hire Charge Invoice",
                        "reference_name": self.name,
                        "cost_center": self.cost_center,
                        "debit_in_account_currency": flt(self.total_invoice_amount),
                        "debit": flt(self.total_invoice_amount),
                        "business_activity": default_ba
                    })

            je.insert()

        self.db_set("invoice_jv", je.name)


    def readjust_advance(self):
        frappe.db.sql("update `tabJournal Entry Account` set reference_type=%s,reference_name=%s where reference_type=%s and reference_name=%s and docstatus = 1", ("Equipment Hiring Form", self.ehf_name, "Hire Charge Invoice", self.name))

    def check_close(self, cancel=0):
        if self.close:
            hire = frappe.get_doc("Equipment Hiring Form", self.ehf_name)
            if cancel:
                hire.db_set("payment_completed", 0)
            else:
                hire.db_set("payment_completed", 1)

    def make_gl_entries(self):
        if self.total_invoice_amount > 0:
            from erpnext.accounts.general_ledger import make_gl_entries
            gl_entries = []
            self.posting_date = self.posting_date
            default_ba = get_default_ba()

        # receivable_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_receivable_account")
        # if not receivable_account:
        # 	frappe.throw("Setup Reveivable Account in Maintenance Accounts Settings")

        credit_account = frappe.db.get_value("Company", "De-Suung", "default_payable_account")
        if not credit_account:
             frappe.throw("Setup Credit Account in Company Accounts Settings")

        advance_account = frappe.db.get_single_value("Maintenance Accounts Settings", "default_advance_account")
        if not advance_account:
            frappe.throw("Setup Advance Account in Maintenance Accounts Settings")

        hire_account = frappe.db.get_single_value("Maintenance Accounts Settings", "hire_revenue_account")
        if not hire_account:
            frappe.throw("Setup Hire Account in Maintenance Accounts Settings")

        hire_expense_account = frappe.db.get_single_value("Maintenance Accounts Settings", "hire_expense_account")
        if not hire_account:
            frappe.throw("Setup Hire Expense Account in Maintenance Accounts Settings")

        discount_account = frappe.db.get_single_value("Maintenance Accounts Settings", "discount_account")
        if not discount_account:
            frappe.throw("Setup Discount Account in Maintenance Accounts Settings")
        
                    
        for a in self.items:
            equip_ba = get_equipment_ba(a.equipment)

            # gl_entries.append(
            # 	self.get_gl_dict({
            # 	       "account": hire_account,
            # 	       "against_voucher_type": "Equipment Hiring Form",
            # 	       "against": self.ehf_name,
            # 	       "credit": a.total_amount,
            # 	       "credit_in_account_currency": a.total_amount,
            # 	       "cost_center": self.cost_center,
            # 	       "business_activity": equip_ba
            # 	}, self.currency)
            # )
            gl_entries.append(
                self.get_gl_dict({
                       "account": hire_expense_account,
                       "against_voucher_type": "Equipment Hiring Form",
                       "against": self.customer,
                       "debit": a.total_amount,
                       "debit_in_account_currency": a.total_amount,
                       "cost_center": self.cost_center,
                       "business_activity": equip_ba
                }, self.currency)
            )

            if a.discount_amount:
                gl_entries.append(
                    self.get_gl_dict({
                           "account": discount_account,
                           "against": self.customer,
                           "debit": a.discount_amount,
                           "debit_in_account_currency": a.discount_amount,
                           "cost_center": self.cost_center,
                           "business_activity": equip_ba
                    }, self.currency)
                )

        if self.advance_amount:
            gl_entries.append(
                self.get_gl_dict({
                       "account": advance_account,
                       "against": self.customer,
                       "party_type": "Supplier",
                       "party": self.customer,
                       "debit": self.advance_amount,
                       "debit_in_account_currency": self.advance_amount,
                       "cost_center": self.cost_center,
                       "business_activity": default_ba
                }, self.currency)
            )
        if self.balance_amount: 
            gl_entries.append(
                    self.get_gl_dict({
                        "account": credit_account,
                        "against_voucher_type": "Equipment Hiring Form",
                        "against": self.customer,
                        "credit": self.balance_amount,
                        "credit_in_account_currency": self.balance_amount,
                        "cost_center": self.cost_center,
                        "business_activity": equip_ba,
                        "party": self.customer,
                        "party_type": "Supplier"
                    }, self.currency)
            )
        # added by phuntsho on march 16 2021
        if self.tds_amount: 
            gl_entries.append(
                    self.get_gl_dict({
                        "account": self.tds_account,
                        "against_voucher_type": "Equipment Hiring Form",
                        "against": self.customer,
                        "credit": self.tds_amount,
                        "credit_in_account_currency": self.tds_amount,
                        "cost_center": self.cost_center,
                        "business_activity": equip_ba
                    }, self.currency)
            )
        make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="No", merge_entries=False)


        # if self.balance_amount:
        # 	gl_entries.append(
        # 		self.get_gl_dict({
        # 		       "account": receivable_account,
        # 		       "against": self.customer,
        # 		       "party_type": "Supplier",
        # 		       "party": self.customer,
        # 		       "against_voucher": self.name,
        # 		       "against_voucher_type": self.doctype,
        # 		       "debit": self.balance_amount,
        # 		       "debit_in_account_currency": self.balance_amount,
        # 		       "cost_center": self.cost_center,
        # 		       "business_activity": default_ba
        # 		}, self.currency)
        # 	)
       
    def commit_budget(self, hire_expense_account):
        commit_bud = frappe.get_doc({
            "doctype": "Committed Budget",
            "account": hire_expense_account,
            "cost_center": self.cost_center,
            "business_activity": self.business_activity,
            "po_no": self.name,
            "po_date": self.posting_date,
            "amount": self.total_invoice_amount,
            "date": frappe.utils.nowdate()
        })
        commit_bud.flags.ignore_permissions=1
        commit_bud.submit()

    def consume_budget(self,hire_expense_account):
        consume = frappe.get_doc({
            "doctype": "Consumed Budget",
            "account": hire_expense_account,
            "cost_center": self.cost_center,
            "po_no": self.name,
            "po_date": self.posting_date,
            "amount": self.total_invoice_amount,
            "business_activity": self.business_activity,
            "date": frappe.utils.nowdate()})
        consume.flags.ignore_permissions = 1
        consume.submit()
    
    def cancel_budget_entry(self):
        frappe.db.sql(
            "delete from `tabCommitted Budget` where po_no = %s", self.name)
        frappe.db.sql(
            "delete from `tabConsumed Budget` where po_no = %s", self.name)

    def refund_of_excess_advance(self):
        revenue_bank_account = frappe.db.get_value("Branch", self.branch, "revenue_bank_account")
        if not revenue_bank_account:
            frappe.throw("Setup Default Revenue Bank Account for your Branch")

        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1 
        je.title = "Advance Refund for Hire Charge Form  (" + self.ehf_name + ")"
        je.voucher_type = 'Bank Entry'
        je.naming_series = 'Bank Payment Voucher'
        je.remark = 'Payment against : ' + self.ehf_name;
        je.posting_date = self.posting_date
        je.branch = self.branch

        total_amount = 0

        for a in self.advances:
            if flt(a.actual_advance_amount) > flt(a.allocated_amount):
                amount = flt(a.actual_advance_amount) - flt(a.allocated_amount)
                total_amount = total_amount + amount
                je.append("accounts", {
                        "account": a.advance_account,
                        "party_type": "Supplier",
                        "party": self.customer,
                        "reference_type": "Hire Charge Invoice",
                        "reference_name": self.name,
                        "cost_center": a.advance_cost_center,
                        "debit_in_account_currency": flt(amount),
                        "debit": flt(amount),
                    })

        if total_amount > 0:
            je.append("accounts", {
                    "account": revenue_bank_account,
                    "cost_center": self.cost_center,
                    "credit_in_account_currency": flt(total_amount),
                    "credit": flt(total_amount),
                })

            je.insert()

            frappe.msgprint("Bill processed to accounts through journal voucher " + je.name)

#@frappe.whitelist()
# by phuntsho on march 13 2021. Rewrite the entire query in order to match the changes made in vehicle logbook. 
# def get_vehicle_logs(form=None):
#     if form:
#         data =  frappe.db.sql("""
#             select 
#                 a.name as name, 
#                 a.registration_number as equipment_number, 
#                 a.equipment as equipment, 
#                 (select b.rate_based_on from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') as rate_type, 
        
#                 a.grand_total_km as total_km,
#                 (select b.rate from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') as rate, 
#                 (case when ((select b.rate_based_on from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') = "Daily") 
#                      THEN
#                         1 * (select b.rate from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') 
#                     ELSE
#                         a.grand_total_km * (select b.rate from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') 
#                 END) as total_amount
#             from
#                 `tabVehicle Logbook` a
#             where 
#                 a.docstatus = 1 and 
#                 a.invoice_created = 0 and 
#                 a.equipment_hiring_form = '{equip_hire_from}'""".format(equip_hire_from = form), as_dict=True)
#         return data
#     else:
#         frappe.throw("Select Equipment Hiring Form first!")
@frappe.whitelist()
def get_vehicle_logs(form=None, branch=None):
    if form:
        data =  frappe.db.sql("""
            select 
                a.name as name, 
                a.registration_number as equipment_number, 
                a.equipment as equipment, 
                (select b.rate_based_on from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') as rate_type, 
                ifnull(a.total_days,0) as total_days,
                a.grand_total_km as total_km,
                (select b.rate from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') as rate, 
                (CASE 
                    WHEN ((select b.rate_based_on from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') = "Daily") 
                    THEN
                        ifnull(a.total_days * (select b.rate from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}'),0)
                    WHEN ((select b.rate_based_on from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}') = "Kilometer") 
                    THEN
                        ifnull(a.grand_total_km * (select b.rate from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}'),0)
                    ELSE
                        ifnull((select b.rate from `tabEquipment Hiring Form` as b where b.equipment = a.equipment and b.name='{equip_hire_from}'),0)
                    END) as total_amount
            from
                `tabVehicle Logbook` a
            where 
                a.docstatus = 1 and 
                a.invoice_created = 0 and 
                a.branch = '{branch}'and 
                a.equipment_hiring_form = '{equip_hire_from}'""".format(equip_hire_from = form, branch=branch), as_dict=True)
        return data
    else:
        frappe.throw("Select Equipment Hiring Form first!")

@frappe.whitelist()
def get_vehicle_accessories(form, equipment):
    if form and equipment:
        data = frappe.db.sql("select accessory1, accessory2, accessory3, accessory4, accessory5, rate1, rate2, rate3, rate4, rate5, irate1, irate2, irate3, irate4, irate5 from `tabHiring Approval Details` where parent = \'" + str(form) + "\' and equipment = \'" + str(equipment) + "\'", as_dict=True)
        accessories = []
        for a in data:
            if a.accessory1:
                accessories.append({"name": a.accessory1, "work": a.rate1, "idle": a.irate1})	
            if a.accessory2:
                accessories.append({"name": a.accessory2, "work": a.rate2, "idle": a.irate2})	
            if a.accessory3:
                accessories.append({"name": a.accessory3, "work": a.rate3, "idle": a.irate3})	
            if a.accessory4:
                accessories.append({"name": a.accessory4, "work": a.rate4, "idle": a.irate4})	
            if a.accessory5:
                accessories.append({"name": a.accessory5, "work": a.rate5, "idle": a.irate5})	
        return accessories
    else:
        frappe.throw("Select Equipment Hiring Form first!")
#Get advances
@frappe.whitelist()
def get_advances(hire_name):
    if hire_name:
        return frappe.db.sql("select t1.name, t1.remark, t2.credit_in_account_currency as amount, t2.account as advance_account, t2.cost_center, t2.name as reference_row from `tabJournal Entry` t1, `tabJournal Entry Account` t2 where t1.name = t2.parent and t2.is_advance = 'Yes' and t1.docstatus = 1 and t2.reference_name = \'" + str(hire_name)  + "\'", as_dict=True)
    else:
        frappe.throw("Select Equipment Hiring Form first!")

# @frappe.whitelist()
# def make_payment_entry(source_name, target_doc=None): 
# 	def update_docs(obj, target, source_parent):
# 		target.posting_date = nowdate()
# 		target.payment_for = "Hire Charge Invoice"
# 		target.actual_amount = obj.outstanding_amount
#                 target.outgoing_account = frappe.db.get_value("Branch", obj.branch, "revenue_bank_account")
# 		target.supplier = obj.customer
#                 target.net_amount = obj.outstanding_amount
#                 # target.actual_amount = obj.outstanding_amount
#                 # target.income_account = frappe.db.get_value("Branch", obj.branch, "revenue_bank_account")

#                 target.append("items", {
#                         "reference_type": "Hire Charge Invoice",
#                         "reference_name": obj.name,
#                         "outstanding_amount": obj.outstanding_amount,
#                         "allocated_amount": obj.outstanding_amount
#                 })
    
# 	doc = get_mapped_doc("Hire Charge Invoice", source_name, {
# 			"Hire Charge Invoice": {
# 				"doctype": "Mechanical Payment",
# 				"field_map": {
# 					"outstanding_amount": "payable_amount",
# 				},
# 				"postprocess": update_docs,
# 				"validation": {"docstatus": ["=", 1]}
# 			},
# 		}, target_doc)
# 	return doc

@frappe.whitelist()
def make_payment_entry(source_name, target_doc=None):
    def update_docs(obj, target, source_parent):
        target.payable_amount = obj.outstanding_amount
        target.posting_date = nowdate()
        target.payment_for = "Hire Charge Invoice"
        target.net_amount = obj.outstanding_amount
        target.actual_amount = obj.outstanding_amount
        target.outgoing_account = frappe.db.get_value("Branch", obj.branch, "expense_bank_account")
        target.supplier = obj.customer
        target.append("items", {
            "reference_type": "Hire Charge Invoice",
            "reference_name": obj.name,
            "outstanding_amount": obj.outstanding_amount,
            "allocated_amount": obj.outstanding_amount
        })
    doc = get_mapped_doc("Hire Charge Invoice", source_name,
    {"Hire Charge Invoice": {
        "doctype": "Mechanical Payment",
        "field_map": {
            "total_amount": "payable_amount"
            },
        "postprocess": update_docs,
        "validation": {"docstatus": ["=", 1]}
        },
    }, target_doc)
    return doc


# added by phuntsho on march 16 2021 to get the specific tds account
@frappe.whitelist()
def get_tds_account(percentage): 
    data = frappe.db.sql("select field, value from `tabSingles` where doctype = 'Accounts Settings'",as_dict=True)
    if percentage == "2": 
        return data[23].value
    elif percentage == "5": 
        return data[25].value
    else: 
        frappe.throw("The only option is 2 percent or 5 percent")

# eval:in_list(["Job Card", "Maintenance Payment", "Hire Charge Invoice"], doc.payment_for)

# Added by Kinley Dorji to update the payment status on august 03/08/2021
@frappe.whitelist()
def get_payment_entry(doc_name, total_amount):
    """ see if there exist a payment entry submitted for the job card """
    payment_entry = """
        SELECT 
            sum(a.net_amount) as total_amount
        FROM 
            `tabMechanical Payment` as a, 
            `tabMechanical Payment Item` as b
        WHERE 
            a.payment_for = "Hire Charge Invoice" and
            b.reference_type = "Hire Charge Invoice" and 
            b.reference_name= '{name}' and 
            b.parent = a.name and 
            a.docstatus = 1""".format(name=doc_name)
    # frappe.msgprint(payment_entry)
    payment_entry = frappe.db.sql(payment_entry, as_dict=1)
    if len(payment_entry) >= 1 and payment_entry[0].total_amount > 0:
        if flt(payment_entry[0].total_amount) == flt(total_amount):
            frappe.db.set_value("Hire Charge Invoice", doc_name, "payment_status", "Paid")
            return ("Paid")
        else:
            frappe.db.set_value("Hire Charge Invoice", doc_name, 'payment_status', "Partially Paid")
            return ("Partially Paid")

    else:
        frappe.db.set_value("Hire Charge Invoice", doc_name, 'payment_status', "Not Paid")
        return ("Not Paid")