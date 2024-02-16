# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, money_in_words, now_datetime, nowdate, getdate
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class Advance(Document):
    def validate(self):
        self.validate_date()
        self.payment_type = "Receive" if self.party_type == "Customer" else "Pay"
        validate_workflow_states(self)

    def on_submit(self):
        if flt(self.advance_amount) > 0.00:
            self.post_journal_entry()

    def validate_date(self):
        if getdate(self.advance_date) > getdate(nowdate()):
            frappe.throw(_("Entry Date cannot be future date"))

    def get_credit_account(self, exp_gl, imprest_advance_account):
        if self.credit_account:
            return self.credit_account
        else:
            return imprest_advance_account if self.advanced_paid_from_imprest_money == 1 else exp_gl,

    def post_journal_entry(self):
        if not self.advance_account:
            frappe.throw(
                _("Advance GL is not set in Advance Type '{}'.".format(self.advance_type))
            )

        adv_gl_det = frappe.db.get_value(
            doctype="Account",
            filters=self.advance_account,
            fieldname=["account_type", "is_an_advance_account"],
            as_dict=True,
        )

        # Fetching Revenue & Expense GLs
        rev_gl, exp_gl = frappe.db.get_value(
            "Branch", self.branch, ["revenue_bank_account", "expense_bank_account"]
        )
        if self.payment_type == "Receive":
            if not rev_gl:
                frappe.throw(
                    _("Revenue GL is not defined for this Branch '{0}'.").format(self.branch),
                    title="Data Missing",
                )
            rev_gl_det = frappe.db.get_value(
                doctype="Account",
                filters=rev_gl,
                fieldname=["account_type", "is_an_advance_account"],
                as_dict=True,
            )
        else:
            if not exp_gl:
                frappe.throw(
                    _("Expense GL is not defined for this Branch '{0}'.").format(self.branch),
                    title="Data Missing",
                )
            exp_gl_det = frappe.db.get_value(
                doctype="Account",
                filters=exp_gl,
                fieldname=["account_type", "is_an_advance_account"],
                as_dict=True,
            )
        imprest_advance_account = frappe.db.get_value("Company", self.company, "imprest_advance_account")
        credit_account = self.get_credit_account(exp_gl, imprest_advance_account)

        # Posting Journal Entry
        accounts = []
        accounts.append(
            {
                "account": self.advance_account,
                "credit_in_account_currency" if self.party_type == "Customer" else "debit_in_account_currency": flt(self.advance_amount),
                "cost_center": self.cost_center,
                "party_check": 1,
                "party_type": self.party_type,
                "party": self.party,
                "account_type": adv_gl_det.account_type,
                "is_advance": "Yes" if adv_gl_det.is_an_advance_account == 1 else "No",
                "reference_type": self.doctype,
                "reference_name": self.name,
            }
        )

        if self.party_type == "Customer":
            accounts.append(
                {
                    "account": rev_gl,
                    "debit_in_account_currency": flt(self.advance_amount),
                    "cost_center": self.cost_center,
                    "party_check": 0,
                    "account_type": rev_gl_det.account_type,
                    "is_advance": "Yes" if rev_gl_det.is_an_advance_account == 1 else "No",
                    "reference_type": "Advance",
                    "reference_doctype": self.name,
                }
            )
        else:
            accounts.append(
                {
                    "account": credit_account,
                    "credit_in_account_currency": flt(self.advance_amount),
                    "cost_center": self.cost_center,
                    "party_type": "Employee" if self.advanced_paid_from_imprest_money == 1 else None,
                    "party": self.imprest_party if self.advanced_paid_from_imprest_money == 1 else None,
                    "party_check": 0,
                    "account_type": exp_gl_det.account_type,
                    "is_advance": "Yes" if exp_gl_det.is_an_advance_account == 1 else "No",
                    "reference_type": "Advance",
                    "reference_doctype": self.name,
                }
            )

        je = frappe.new_doc("Journal Entry")

        naming_series = ""
        if self.advanced_paid_from_imprest_money == 1 and self.payment_type == "Pay":
            naming_series = "Journal Voucher"
        elif self.advanced_paid_from_imprest_money == 0 and self.payment_type == "Pay":
            naming_series = "Bank Payment Voucher"
        else:
            naming_series = "Bank Receipt Voucher"

        je.update(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Journal Entry" if self.advanced_paid_from_imprest_money == 1 else "Bank Entry",
                "naming_series": naming_series,
                "title": "Advance Paid to " + self.party,
                "user_remark": self.remarks,
                "posting_date": nowdate(),
                "company": self.company,
                "total_amount_in_words": money_in_words(self.advance_amount),
                "accounts": accounts,
                "mode_of_payment": "Adjustment Entry" if self.advanced_paid_from_imprest_money == 1 else "Online Payment",
                "branch": self.branch,
                "reference_type": self.doctype,
                "reference_doctype": self.name,
            }
        )

        if self.advance_amount:
            je.save(ignore_permissions=True)
            self.db_set("journal_entry", je.name)
            self.db_set(
                "journal_entry_status",
                "Forwarded to accounts for processing payment on {0}".format(
                    now_datetime().strftime("%Y-%m-%d %H:%M:%S")
                ),
            )
            frappe.msgprint(
                _("{} posted to accounts").format(frappe.get_desk_link(je.doctype, je.name))
            )
