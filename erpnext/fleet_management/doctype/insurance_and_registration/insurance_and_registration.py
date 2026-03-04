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
        self.calculate_totals()
        self.validate_gst_settings()
    
    def calculate_totals(self):
        """Calculate net_total and gst_amount based on child tables"""
        net_total = 0
        
        if self.items:
            for item in self.items:
                net_total += flt(item.get('amount', 0))
                net_total += flt(item.get('penalty_amount', 0))
                item.total_amount=flt(item.get('amount', 0)) + flt(item.get('penalty_amount', 0))


        
        if self.claim_item:
            for claim in self.claim_item:
                net_total += flt(claim.get('claim_amount', 0))
        
        if self.insurance_item:
            for insurance in self.insurance_item:
                net_total += flt(insurance.get('total_amount', 0))
        
        if self.registration_item:
            for reg in self.registration_item:
                net_total += flt(reg.get('registration_amount', 0))
        
        self.net_total = net_total
        
        if self.apply_gst and self.taxes_and_charges and self.net_total > 0:
            tax_template = frappe.get_doc("Purchase Taxes and Charges Template", self.taxes_and_charges)
            if tax_template.taxes:
                tax_rate = flt(tax_template.taxes[0].rate or 0)
                self.gst_amount = (self.net_total * tax_rate) / 100
                
                if not self.gst_account and tax_template.taxes[0].account_head:
                    self.gst_account = tax_template.taxes[0].account_head
            else:
                self.gst_amount = 0
        else:
            self.gst_amount = 0
    
    def validate_gst_settings(self):
        """Validate GST settings"""
        if self.apply_gst:
            if not self.taxes_and_charges:
                frappe.throw(_("Please select a Taxes and Charges Template when applying GST"))
            
            if not self.gst_account:
                frappe.throw(_("Please select a GST Account"))
    
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
    def get_tax_details(self):
        """Get tax details from selected template"""
        if not self.taxes_and_charges:
            return {}
        
        tax_template = frappe.get_doc("Purchase Taxes and Charges Template", self.taxes_and_charges)
        tax_details = {}
        
        if tax_template.taxes:
            # Get the first tax (assuming it's GST)
            tax = tax_template.taxes[0]
            tax_details = {
                'gst_account': tax.account_head,
                'tax_rate': tax.rate,
                'gst_amount': (self.net_total * tax.rate) / 100 if self.net_total else 0
            }
        
        return tax_details

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

        # Add GST amount to the total if apply_gst is checked
        total_amount = flt(args.total_amount)
        if self.apply_gst:
            total_amount += flt(self.gst_amount)
        
        if flt(total_amount) <= 0:
            frappe.throw(_("Amount should be greater than zero"))

        default_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
        imprest_advance_account = frappe.db.get_value(
            "Company", self.company, "imprest_advance_account"
        )
        if self.settle_imprest_advance == 1 and not imprest_advance_account:
            frappe.throw("Please set Imprest Advance Account in company settings")
        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1
        if args.get("type") == "Insurance":
            category = frappe.db.get_value("Equipment", self.equipment, "equipment_category")
            debit_account = frappe.db.get_value("Equipment Category", category, "insurance_account")

            if not debit_account:
                frappe.throw("Insurance account not set in equipment category {0}".format(category))
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
                "total_amount_in_words": money_in_words(total_amount),
                "branch": self.branch,
                "total_debit": total_amount,
                "total_credit": total_amount,
                "settle_project_imprest": self.settle_imprest_advance,
            }
        )
        je.append(
            "accounts",
            {
                "account": debit_account,
                "debit_in_account_currency": total_amount,
                "debit": total_amount,
                "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                "party_check": 0,
                "party_type": "Supplier",
                "party": args.party,
                "reference_type": self.doctype,
                "reference_name": self.name,
            },
        )
        
        # If GST is applied, add GST account entry
        if self.apply_gst and self.gst_account and flt(self.gst_amount) > 0:
            je.append(
                "accounts",
                {
                    "account": self.gst_account,
                    "debit_in_account_currency": flt(self.gst_amount),
                    "debit": flt(self.gst_amount),
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
                    "credit_in_account_currency": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
                    "credit": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
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
                    "credit_in_account_currency": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
                    "credit": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
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

    @frappe.whitelist()
    def post_to_account(self, args):
        if args.journal_entry and frappe.db.exists("Journal Entry", args.journal_entry):
            doc = frappe.get_doc("Journal Entry", args.journal_entry)
            if doc.docstatus != 2:
                frappe.throw(
                    "Journal Entry exists for this transaction {}".format(
                        frappe.get_desk_link("Journal Entry", args.journal_entry)
                    )
                )

        # Add GST amount to the total if apply_gst is checked
        total_amount = flt(args.registration_amount)
        if self.apply_gst:
            total_amount += flt(self.gst_amount)
        
        if flt(total_amount) <= 0:
            frappe.throw(_("Amount should be greater than zero"))

        default_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
        imprest_advance_account = frappe.db.get_value(
            "Company", self.company, "imprest_advance_account"
        )
        if self.settle_imprest_advance == 1 and not imprest_advance_account:
            frappe.throw("Please set Imprest Advance Account in company settings")

        debit_account = frappe.db.get_single_value("Maintenance Settings", "registration_account")
        if not debit_account:
            frappe.throw("Please set Account in maintenance settings")

        # Posting to JE
        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1
        je.update(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Bank Entry" if self.settle_imprest_advance == 0 else "Journal Entry",
                "naming_series": "Bank Payment Voucher" if self.settle_imprest_advance == 0 else "Journal Voucher",
                "title": " Registration - " + self.equipment,
                "user_remark": "Note: Registration paid against Vehicle "+ self.equipment,
                "posting_date": args.registration_date,
                "company": self.company,
                "total_amount_in_words": money_in_words(total_amount),
                "branch": self.branch,
                "total_debit": total_amount,
                "total_credit": total_amount,
                "settle_project_imprest": self.settle_imprest_advance,
            }
        )
        je.append("accounts",
            {
                "account": debit_account,
                "debit_in_account_currency": total_amount,
                "debit": total_amount,
                "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                "party_check": 0,
                "party_type": "Supplier",
                "party": args.party,
                "reference_type": self.doctype,
                "reference_name": self.name,
            },
        )
        
        # If GST is applied, add GST account entry
        if self.apply_gst and self.gst_account and flt(self.gst_amount) > 0:
            je.append(
                "accounts",
                {
                    "account": self.gst_account,
                    "debit_in_account_currency": flt(self.gst_amount),
                    "debit": flt(self.gst_amount),
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
                    "credit_in_account_currency": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
                    "credit": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
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
                    "credit_in_account_currency": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
                    "credit": total_amount + (flt(self.gst_amount) if self.apply_gst else 0),
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
    @frappe.whitelist()
    def post_je(self):
        if self.reference:
            frappe.throw(
                "Journal Entry exists for this transaction {}".format(
                    frappe.get_desk_link("Journal Entry", self.reference)
                )
            )
        
        # Calculate total amount from all tables
        total_amount = 0.00
        
        # From Bluebook and Emission table
        for i in self.items:
            total_amount += flt(i.amount or 0)
            total_amount += flt(i.penalty_amount or 0)
        
        # From Claim Details table
        for claim in self.claim_item:
            total_amount += flt(claim.claim_amount or 0)
        
        # From Insurance Details table
        for insurance in self.insurance_item:
            total_amount += flt(insurance.total_amount or 0)
        
        # From Registration Details table
        for reg in self.registration_item:
            total_amount += flt(reg.registration_amount or 0)
        
        # Add GST amount if apply_gst is checked
        if self.apply_gst:
            total_amount += flt(self.gst_amount)
        
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
                "title": "Insurance and Registration Charges - " + self.equipment,
                "user_remark": "Note: Insurance and Registration Charges paid against Vehicle "
                + self.equipment,
                "posting_date": posting_date,
                "company": self.company,
                "branch": self.branch,
                "settle_project_imprest": self.settle_imprest_advance,
            }
        )
        
        # ============ DEBIT ENTRIES ============
        
        # 1. Debit entries for Bluebook, Emission, Fitness, Offense
        for item in self.items:
            account = ""
            if item.get("type") == "Bluebook":
                account = frappe.db.get_single_value("Maintenance Settings", "bluebook")
            elif item.get("type") == "Emission":
                account = frappe.db.get_single_value("Maintenance Settings", "emission")
            elif item.get("type") == "Fitness":
                account = frappe.db.get_single_value("Maintenance Settings", "fitness")
            elif item.get("type") == "Offense":
                account = frappe.db.get_single_value("Maintenance Settings", "offense")
            
            if not account:
                frappe.throw(
                    "GL not set in maintenance setting for type {} ".format(item.get("type"))
                )
            
            # Add main amount entry
            if flt(item.amount or 0) > 0:
                je.append(
                    "accounts",
                    {
                        "account": account,
                        "debit_in_account_currency": flt(item.amount or 0),
                        "debit": flt(item.amount or 0),
                        "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                        "party_check": 0,
                        "party_type": "Supplier" if item.party else None,
                        "party": item.party if item.party else None,
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                    },
                )
            
            # Add penalty amount entry if exists
            if flt(item.penalty_amount or 0) > 0:
                je.append(
                    "accounts",
                    {
                        "account": fine_and_penalty_account,
                        "debit_in_account_currency": flt(item.penalty_amount or 0),
                        "debit": flt(item.penalty_amount or 0),
                        "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                        "party_check": 0,
                        "party_type": "Supplier" if item.party else None,
                        "party": item.party if item.party else None,
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                    },
                )
        
        # 2. Debit entries for Claim Details
        for claim in self.claim_item:
            if flt(claim.claim_amount or 0) > 0:
                # Get claim account from equipment category
                if self.equipment:
                    category = frappe.db.get_value("Equipment", self.equipment, "equipment_category")
                    claim_account = frappe.db.get_value("Equipment Category", category, "insurance_account")
                    
                    if not claim_account:
                        frappe.throw(f"Insurance account not set in equipment category {category}")
                
                je.append(
                    "accounts",
                    {
                        "account": claim_account,
                        "debit_in_account_currency": flt(claim.claim_amount or 0),
                        "debit": flt(claim.claim_amount or 0),
                        "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                        "party_check": 0,
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                    },
                )
        
        # 3. Debit entries for Insurance Details
        for insurance in self.insurance_item:
            if flt(insurance.total_amount or 0) > 0:
                # Get insurance account from equipment category
                if self.equipment:
                    category = frappe.db.get_value("Equipment", self.equipment, "equipment_category")
                    insurance_account = frappe.db.get_value("Equipment Category", category, "insurance_account")
                    
                    if not insurance_account:
                        frappe.throw(f"Insurance account not set in equipment category {category}")
                
                je.append(
                    "accounts",
                    {
                        "account": insurance_account,
                        "debit_in_account_currency": flt(insurance.total_amount or 0),
                        "debit": flt(insurance.total_amount or 0),
                        "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                        "party_check": 0,
                        "party_type": "Supplier" if insurance.party else None,
                        "party": insurance.party if insurance.party else None,
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                    },
                )
        
        # 4. Debit entries for Registration Details
        for reg in self.registration_item:
            if flt(reg.registration_amount or 0) > 0:
                # Get registration account from Maintenance Settings
                registration_account = frappe.db.get_single_value("Maintenance Settings", "registration_account")
                
                if not registration_account:
                    frappe.throw("Please set registration account in Maintenance Settings")
                
                je.append(
                    "accounts",
                    {
                        "account": registration_account,
                        "debit_in_account_currency": flt(reg.registration_amount or 0),
                        "debit": flt(reg.registration_amount or 0),
                        "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                        "party_check": 0,
                        "party_type": "Supplier" if reg.party else None,
                        "party": reg.party if reg.party else None,
                        "reference_type": self.doctype,
                        "reference_name": self.name,
                    },
                )
        
        # 5. GST Account entry if apply_gst is checked
        if self.apply_gst and self.gst_account and flt(self.gst_amount or 0) > 0:
            je.append(
                "accounts",
                {
                    "account": self.gst_account,
                    "debit_in_account_currency": flt(self.gst_amount or 0),
                    "debit": flt(self.gst_amount or 0),
                    "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                    "reference_type": self.doctype,
                    "reference_name": self.name,
                },
            )
        
        # Calculate total debit amount
        total_debit = sum([flt(acc.debit or 0) for acc in je.accounts])
        
        # ============ CREDIT ENTRIES ============
        
        # Credit entry (Bank or Imprest Advance)
        if self.settle_imprest_advance == 0:
            je.append(
                "accounts",
                {
                    "account": default_bank_account,
                    "credit_in_account_currency": total_debit,
                    "credit": total_debit,
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
                    "credit_in_account_currency": total_debit,
                    "credit": total_debit,
                    "cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
                },
            )
        
        # Update JE totals
        je.total_debit = total_debit
        je.total_credit = total_debit
        je.total_amount_in_words = money_in_words(total_debit)
        
        je.insert()
        frappe.msgprint(
            _("Journal Entry {0} posted to accounts").format(
                frappe.get_desk_link("Journal Entry", je.name)
            )
        )
        frappe.db.set_value("Insurance and Registration", self.name, "reference", je.name)
        return je.name