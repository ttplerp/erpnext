# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, money_in_words
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from erpnext.accounts.party import get_party_account


class InsuranceandRegistration(Document):
    def validate(self):
        self.prevent_row_remove()

    def prevent_row_remove(self):
        unsafed_record = [d.name for d in self.insurance_item]
        if flt(len(unsafed_record)) <= 0:
            unsafed_record = ["Dummy"]
        for d in frappe.db.sql(
            "select name, journal_entry, idx from `tabInsurance Details` where parent = '{}'".format(
                self.name
            ),
            as_dict=True,
        ):
            if d.name not in unsafed_record and d.journal_entry:
                je = frappe.get_doc("Journal Entry", d.journal_entry)
                if je.docstatus != 2:
                    frappe.throw(
                        "You cannot delete row {} from Insurance Detail as \
						accounting entry is booked".format(
                            frappe.bold(d.idx)
                        )
                    )

        unsafed_record = [d.name for d in self.items]
        if flt(len(unsafed_record)) <= 0:
            unsafed_record = ["Dummy"]
        for d in frappe.db.sql(
            "select name, journal_entry, idx from `tabBluebook and Emission` where parent = '{}'".format(
                self.name
            ),
            as_dict=True,
        ):
            if d.name not in unsafed_record and d.journal_entry:
                je = frappe.get_doc("Journal Entry", d.journal_entry)
                if je.docstatus != 2:
                    frappe.throw(
                        "You cannot delete row {} from Bluebook Fitness \
							and Emission Details as accounting entry is booked".format(
                            frappe.bold(d.idx)
                        )
                    )

    @frappe.whitelist()
    def create_je(self, args):
        if args.journal_entry and frappe.db.exists("Journal Entry", args.journal_entry):
            doc = frappe.get_doc("Journal Entry", args.journal_entry)
            if doc.docstatus != 2:
                frappe.throw(
                    "Journal Entry exists for this transaction {}".format(
                        frappe.get_desk_link("Journal Entry", args.journal_entry)
                    )
                )

        if flt(args.total_amount) <= 0:
            frappe.throw(_("Amount should be greater than zero"))

        default_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
        imprest_advance_account = frappe.db.get_value(
            "Company", self.company, "imprest_advance_account"
        )
        if self.settle_imprest_advance == 1 and not imprest_advance_account:
            frappe.throw("Please set Imprest Advance Account in company settings")
        # Posting Journal Entry
        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1
        if args.get("type") == "Insurance":
            debit_account = get_party_account(
                "Supplier", args.get("party"), self.company, is_advance=True
            )
            posting_date = args.get("insured_date")
        else:
            posting_date = args.get("receipt_date")
            debit_account = frappe.db.get_value(
                "Company", self.company, "repair_and_service_expense_account"
            )
            if not debit_account:
                frappe.throw("Setup Fleet Expense Account in Company".format())
        if not default_bank_account:
            frappe.throw("Setup Default Bank Account in Branch {}".format(self.branch))

        je.update(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Bank Entry"
                if self.settle_imprest_advance == 0
                else "Journal Entry",
                "naming_series": "Bank Payment Voucher"
                if self.settle_imprest_advance == 0
                else "Journal Voucher",
                "title": args.type + " Charge - " + self.equipment,
                "user_remark": "Note: "
                + args.type
                + " Charge paid against Vehicle "
                + self.equipment,
                "posting_date": posting_date,
                "company": self.company,
                "total_amount_in_words": money_in_words(args.total_amount),
                "branch": self.branch,
                "total_debit": args.total_amount,
                "total_credit": args.total_amount,
                "settle_project_imprest": self.settle_imprest_advance,
            }
        )
        je.append(
            "accounts",
            {
                "account": debit_account,
                "debit_in_account_currency": args.total_amount,
                "debit": args.total_amount,
                "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                "party_check": 0,
                "party_type": "Supplier",
                "party": args.party,
                "reference_type": self.doctype,
                "reference_name": self.name,
            },
        )
        if self.settle_imprest_advance == 0:
            je.append(
                "accounts",
                {
                    "account": default_bank_account,
                    "credit_in_account_currency": args.total_amount,
                    "credit": args.total_amount,
                    "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                },
            )
        else:
            je.append(
                "accounts",
                {
                    "account": imprest_advance_account,
                    "party_type": "Employee",
                    "party": self.imprest_party,
                    "credit_in_account_currency": args.total_amount,
                    "credit": args.total_amount,
                    "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                },
            )
        je.insert()
        frappe.msgprint(
            _("Journal Entry {0} posted to accounts").format(
                frappe.get_desk_link("Journal Entry", je.name)
            )
        )
        return je.name
        # Set a reference to the claim journal entry

    @frappe.whitelist()
    def post_je(self):
        if self.reference:
            frappe.throw(
                "Journal Entry exists for this transaction {}".format(
                    frappe.get_desk_link("Journal Entry", self.reference)
                )
            )
        if len(self.items) <= 0:
            frappe.throw(_("There must be at least one or more item in the table"))

        total_amount = 0.00
        for i in self.items:
            total_amount += flt(i.total_amount)

        if flt(total_amount) <= 0:
            frappe.throw(_("Amount should be greater than zero"))

        default_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
        imprest_advance_account = frappe.db.get_value(
            "Company", self.company, "imprest_advance_account"
        )
        if self.settle_imprest_advance == 1 and not imprest_advance_account:
            frappe.throw("Please set Imprest Advance Account in company settings")
        # Posting Journal Entry
        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1
        posting_date = self.get("posting_date")
        # debit_account = frappe.db.get_value(
        #     "Company", self.company, "repair_and_service_expense_account"
        # )
        # if not debit_account:
        #     frappe.throw("Setup Fleet Expense Account in Company".format())
        if not default_bank_account:
            frappe.throw("Setup Default Bank Account in Branch {}".format(self.branch))

        fine_and_penalty_account = frappe.db.get_value(
            "Company", self.company, "fine_and_penalty_account"
        )

        if not fine_and_penalty_account:
            frappe.throw("Fines and Penalty Account not set in company setting")

        je.update(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Bank Entry"
                if self.settle_imprest_advance == 0
                else "Journal Entry",
                "naming_series": "Bank Payment Voucher"
                if self.settle_imprest_advance == 0
                else "Journal Voucher",
                "title": " Bluebook Fitness and Emission Charge - " + self.equipment,
                "user_remark": "Note: Bluebook Fitness and Emission Charge "
                + " Charge paid against Vehicle "
                + self.equipment,
                "posting_date": posting_date,
                "company": self.company,
                "total_amount_in_words": money_in_words(total_amount),
                "branch": self.branch,
                "total_debit": total_amount,
                "total_credit": total_amount,
                "settle_project_imprest": self.settle_imprest_advance,
            }
        )
        # debit
        for args in self.items:
            account = ""
            if args.get("type") == "Bluebook":
                account = frappe.db.get_single_value("Maintenance Settings", "bluebook")
            elif args.get("type") == "Emission":
                account = frappe.db.get_single_value("Maintenance Settings", "emission")
            elif args.get("type") == "Fitness":
                account = frappe.db.get_single_value("Maintenance Settings", "fitness")

            if not account:
                frappe.throw(
                    "GL not set in maintenance setting for type {} ".format(args.get("type"))
                )

            je.append(
                "accounts",
                {
                    "account": account,
                    "debit_in_account_currency": args.amount,
                    "debit": args.amount,
                    "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                    "party_check": 0,
                    "party_type": "Supplier",
                    "party": args.party,
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                },
            )

            if args.penalty_amount > 0:
                je.append(
                    "accounts",
                    {
                        "account": fine_and_penalty_account,
                        "debit_in_account_currency": args.penalty_amount,
                        "debit": args.penalty_amount,
                        "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                        "party_check": 0,
                        "party_type": "Supplier",
                        "party": args.party,
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                    },
                )

        if self.settle_imprest_advance == 0:
            je.append(
                "accounts",
                {
                    "account": default_bank_account,
                    "credit_in_account_currency": total_amount,
                    "credit": total_amount,
                    "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
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
                    "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                },
            )
        je.insert()
        frappe.msgprint(
            _("Journal Entry {0} posted to accounts").format(
                frappe.get_desk_link("Journal Entry", je.name)
            )
        )
        frappe.db.set_value("Insurance and Registration", self.name, "reference", je.name)
        return je.name
