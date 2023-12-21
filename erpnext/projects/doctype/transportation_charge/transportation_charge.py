# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, money_in_words
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from erpnext.accounts.general_ledger import (
    make_gl_entries,
    merge_similar_entries,
)


class TransportationCharge(AccountsController):
    def validate(self):
        validate_workflow_states(self)
        notify_workflow_states(self)

    def on_submit(self):
        self.make_gl_entries()
        self.make_journal_entry()
        notify_workflow_states(self)

    def on_cancel(self):
        self.make_gl_entries()
        self.make_journal_entry(cancel=True)

    def make_gl_entries(self):
        gl_entries = []
        self.make_supplier_gl_entry(gl_entries)
        self.make_carriage_gl_entry(gl_entries)
        gl_entries = merge_similar_entries(gl_entries)
        make_gl_entries(gl_entries, update_outstanding="No", cancel=self.docstatus == 2)

    def make_supplier_gl_entry(self, gl_entries):
        carriage_payable = frappe.db.get_single_value("Projects Settings", "carriage_payable")
        if not carriage_payable:
            frappe.throw("Carriage payable not set project settings")
        for i in self.items:
            if flt(i.total_amount) > 0 and i.party_type == "Supplier":
                gl_entries.append(
                    self.get_gl_dict(
                        {
                            "account": carriage_payable,
                            "credit": flt(i.total_amount, 2),
                            "credit_in_account_currency": flt(i.total_amount, 2),
                            "against_voucher": self.name,
                            "party_type": i.party_type,
                            "party": i.party,
                            "against_voucher_type": self.doctype,
                            "cost_center": i.cost_center,
                            "voucher_type": self.doctype,
                            "voucher_no": self.name,
                        },
                        self.currency,
                    )
                )

    def make_carriage_gl_entry(self, gl_entries):
        carriage_charge = frappe.db.get_single_value("Projects Settings", "carriage_charge")
        if not carriage_charge:
            frappe.throw("Carriage charge not set project settings")
        for i in self.items:
            if flt(i.total_amount) > 0:
                gl_entries.append(
                    self.get_gl_dict(
                        {
                            "account": carriage_charge,
                            "debit": flt(i.total_amount, 2),
                            "debit_in_account_currency": flt(i.total_amount, 2),
                            "against_voucher": self.name,
                            "party_type": i.party_type,
                            "party": i.party,
                            "against_voucher_type": self.doctype,
                            "cost_center": i.cost_center,
                            "voucher_type": self.doctype,
                            "voucher_no": self.name,
                        },
                        self.currency,
                    )
                )

    def make_journal_entry(self, cancel=None):
        if cancel:
            frappe.db.set_value("Journal Entry", self.journal_entry, "docstatus", 2)
            return

        if self.journal_entry and frappe.db.exists("Journal Entry", self.journal_entry):
            doc = frappe.get_doc("Journal Entry", self.journal_entry)
            if doc.docstatus != 2:
                frappe.throw(
                    "Journal Entry exists for this transaction {}".format(
                        frappe.get_desk_link("Journal Entry", self.journal_entry)
                    )
                )
        carriage_charge = frappe.db.get_single_value("Projects Settings", "carriage_charge")
        if not carriage_charge:
            frappe.throw("Carriage charge not set project settings")

        carriage_payable = frappe.db.get_single_value("Projects Settings", "carriage_payable")
        if not carriage_payable:
            frappe.throw("Carriage payable not set project settings")

        imprest_advance_account = frappe.db.get_value(
            "Company", self.company, "imprest_advance_account"
        )
        if not imprest_advance_account:
            frappe.throw("Imprest Advance Account not set company settings")

        total_amount = 0.00
        for i in self.items:
            total_amount += flt(i.total_amount)

        if total_amount <= 0:
            frappe.throw("The total amount must be greater than 0")

        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1
        je.update(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Journal Entry"
                if self.settle_imprest_advance == 1
                else "Bank Entry",
                "naming_series": "Journal Voucher"
                if self.settle_imprest_advance == 1
                else "Bank Payment Voucher",
                "title": "Transportation charge",
                "user_remark": "Note: Transportation charge - against " + str(self.cost_center),
                "posting_date": self.posting_date,
                "company": self.company,
                "total_amount_in_words": money_in_words(total_amount),
                "branch": self.branch,
                "total_debit": total_amount,
                "total_credit": total_amount,
            }
        )
        for i in self.items:
            je.append(
                "accounts",
                {
                    "account": carriage_payable,
                    "debit_in_account_currency": i.total_amount,
                    "debit": i.total_amount,
                    "cost_center": i.cost_center,
                    "party_check": 0,
                    "party_type": i.party_type,
                    "party": i.party,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                },
            )
        if self.settle_imprest_advance == 0:
            default_bank_account = frappe.db.get_value(
                "Company", self.company, "default_bank_account"
            )
            if not default_bank_account:
                frappe.throw("Default Bank Account not set Company")

            je.append(
                "accounts",
                {
                    "account": default_bank_account,
                    "credit_in_account_currency": total_amount,
                    "credit": total_amount,
                    "cost_center": self.cost_center,
                },
            )
        else:
            je.append(
                "accounts",
                {
                    "account": imprest_advance_account,
                    "party_type": "Employee",
                    "party": self.imprest_party,
                    "credit_in_account_currency": total_amount,
                    "credit": total_amount,
                    "cost_center": self.cost_center,
                },
            )

        je.insert()
        frappe.msgprint(
            _("Journal Entry {0} posted to accounts").format(
                frappe.get_desk_link("Journal Entry", je.name)
            )
        )
        frappe.db.set_value(self.doctype, self.name, "journal_entry", je.name)
