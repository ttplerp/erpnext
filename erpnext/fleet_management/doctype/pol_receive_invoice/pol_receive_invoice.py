# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt, money_in_words, now_datetime
from erpnext.accounts.party import get_party_account
from erpnext.accounts.general_ledger import (
    make_gl_entries,
)
from erpnext.controllers.accounts_controller import AccountsController

class POLReceiveInvoice(AccountsController):
    def validate(self):
        self.fetch_details_from_pol_receive()
        self.calculate_outstanding_amount()
        self.set_status()
        if not self.credit_account:
            self.credit_account = get_party_account(self.party_type, self.party, self.company)
        if not self.cost_center and self.branch:
            self.cost_center = frappe.db.get_value("Branch", self.branch, "cost_center")

    def fetch_details_from_pol_receive(self):
        """Fetch all details including taxes from POL Receive"""
        if self.reference_name:
            try:
                pol_receive = frappe.get_doc("POL Receive", self.reference_name)
                
                # Copy basic fields
                self.company = pol_receive.company
                self.branch = pol_receive.branch
                self.posting_date = pol_receive.posting_date
                self.cost_center = pol_receive.cost_center
                
                # Copy party details
                self.party_type = "Supplier"
                self.party = pol_receive.paid_to
                
                # Copy amount details
                self.amount = flt(pol_receive.total_amount or 0)
                self.net_total = flt(pol_receive.net_total or 0)
                
                # Set amount_after_gst and grand_total
                self.amount_after_gst = flt(pol_receive.grand_total or 0)
                self.grand_total = flt(pol_receive.grand_total or 0)
                
                # Copy taxes table from POL Receive to POL Receive Invoice
                self.copy_taxes_from_pol_receive(pol_receive)
                
                # Calculate GST amount from taxes table
                self.calculate_gst_amount_from_taxes()
                
                # Set debit account based on equipment type
                self.set_debit_account(pol_receive)
                
                # Set credit account if not set
                if not self.credit_account:
                    self.credit_account = frappe.db.get_value("Company", self.company, "default_payable_account")
                
                # Set GST account from GST tax rows
                self.set_gst_account_from_taxes()
                
            except frappe.DoesNotExistError:
                frappe.throw(_("Linked POL Receive {0} does not exist").format(self.reference_name))
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), "POL Receive Invoice Fetch Error")
                frappe.throw(_("Error fetching details from POL Receive: {0}").format(str(e)))
        else:
            # Set defaults if no reference
            if not self.gst_amount:
                self.gst_amount = 0
            if not self.amount_after_gst:
                self.amount_after_gst = self.amount
            if not self.net_total:
                self.net_total = self.amount
            if not self.grand_total:
                self.grand_total = self.amount

    def calculate_gst_amount_from_taxes(self):
        """Calculate total GST amount from taxes table"""
        total_gst = 0
        if self.taxes:
            for tax in self.taxes:
                account_head = tax.account_head or ""
                description = tax.description or ""
                
                # Check if this is a GST tax
                is_gst = (tax.get("is_gst") or 
                         'GST' in account_head.upper() or 
                         'GST' in description.upper())
                
                if is_gst and tax.add_deduct_tax == "Add":
                    total_gst += flt(tax.tax_amount or 0)
        
        self.gst_amount = total_gst

    def copy_taxes_from_pol_receive(self, pol_receive):
        """Copy all taxes from POL Receive to POL Receive Invoice"""
        if hasattr(pol_receive, 'taxes') and pol_receive.taxes:
            # Clear existing taxes
            self.set('taxes', [])
            
            # Copy each tax row
            for tax in pol_receive.taxes:
                tax_row = self.append('taxes', {})
                
                # Copy all relevant fields
                tax_row.category = tax.category
                tax_row.add_deduct_tax = tax.add_deduct_tax
                tax_row.charge_type = tax.charge_type
                tax_row.row_id = tax.row_id
                tax_row.account_head = tax.account_head
                tax_row.description = tax.description
                tax_row.rate = flt(tax.rate or 0)
                tax_row.tax_amount = flt(tax.tax_amount or 0)
                tax_row.total = flt(tax.total or 0)
                tax_row.cost_center = tax.cost_center or self.cost_center
                
                # Copy additional fields
                tax_row.included_in_print_rate = tax.included_in_print_rate
                tax_row.is_gst = tax.is_gst
                tax_row.account_currency = tax.account_currency
                
                # Copy base amounts
                tax_row.base_tax_amount = flt(tax.base_tax_amount or 0)
                tax_row.base_total = flt(tax.base_total or 0)
                
                # Copy party details if present
                tax_row.party = tax.party
                tax_row.imprest_settlement = tax.imprest_settlement
                tax_row.imprest_party = tax.imprest_party
                
                # Copy reference fields
                tax_row.reference_type = tax.reference_type
                tax_row.reference_no = tax.reference_no
                
                # Copy item wise tax detail
                if tax.item_wise_tax_detail:
                    tax_row.item_wise_tax_detail = tax.item_wise_tax_detail
                
                # Copy payable to different vendor details
                tax_row.payable_to_different_vendor = tax.payable_to_different_vendor
                tax_row.amount_paid_to_different_vendors = flt(tax.amount_paid_to_different_vendors or 0)
            
            frappe.msgprint(
                _("Copied {0} tax row(s) from POL Receive").format(len(pol_receive.taxes)),
                alert=True
            )

    def set_debit_account(self, pol_receive):
        """Set debit account based on equipment type"""
        if not self.debit_account:
            # Case 1: Hired Equipment
            if pol_receive.get("hired_equipment"):
                if pol_receive.get("fuel_policy") == "Without Fuel":
                    return
                
                if pol_receive.get("hired_equipment_type") == "Machine":
                    self.debit_account = frappe.db.get_single_value(
                        "Maintenance Settings", 
                        "machine_expense_account"
                    )
                elif pol_receive.get("hired_equipment_type") == "Vehicle":
                    self.debit_account = frappe.db.get_single_value(
                        "Maintenance Settings", 
                        "vehicle_expense_account"
                    )
            
            # Case 2: Own Equipment
            elif pol_receive.get("equipment"):
                if pol_receive.get("direct_consumption"):
                    self.debit_account = frappe.db.get_value(
                        "Equipment Category", 
                        pol_receive.get("equipment_category"), 
                        "pol_advance_account"
                    )
                else:
                    self.debit_account = frappe.db.get_value(
                        "Equipment Category", 
                        pol_receive.get("equipment_category"), 
                        "pol_receive_account"
                    )
            
            # Case 3: Barrel Receipt
            elif pol_receive.get("receive_in_barrel") == 1:
                self.debit_account = frappe.db.get_value(
                    "Warehouse", 
                    pol_receive.get("warehouse"), 
                    "account"
                )

    def set_gst_account_from_taxes(self):
        """Extract GST account from taxes table"""
        if self.taxes:
            gst_accounts = []
            for tax in self.taxes:
                account_head = tax.account_head or ""
                description = tax.description or ""
                
                is_gst = (tax.get("is_gst") or 
                         'GST' in account_head.upper() or 
                         'GST' in description.upper() or 
                         'TAX' in account_head.upper())
                
                if is_gst and account_head and account_head not in gst_accounts:
                    gst_accounts.append(account_head)
            
            if gst_accounts:
                self.gst_account = ", ".join(gst_accounts)
            elif self.gst_amount > 0:
                frappe.msgprint(
                    _("GST amount ({0}) found but no GST accounts identified in taxes table.").format(
                        self.gst_amount
                    ),
                    alert=True
                )

    def calculate_outstanding_amount(self):
        """Calculate outstanding amount"""
        if self.amount_after_gst:
            self.outstanding_amount = flt(self.amount_after_gst)
        elif self.grand_total:
            self.outstanding_amount = flt(self.grand_total)
        else:
            self.outstanding_amount = flt(self.amount)

    def set_status(self, update=False, status=None, update_modified=True):
        """Set document status"""
        outstanding_amount = flt(self.outstanding_amount, 2)
        
        if not status:
            if self.docstatus == 2:
                status = "Cancelled"
            elif self.docstatus == 1:
                if outstanding_amount > 0:
                    status = "Unpaid"
                elif outstanding_amount <= 0:
                    status = "Paid"
                else:
                    status = "Submitted"
            else:
                status = "Draft"
        
        self.status = status
        
        if update:
            self.db_set("status", self.status, update_modified=update_modified)

    def validate_accounting_entries(self):
        """Validate accounting entries before submission"""
        if not self.debit_account:
            frappe.throw(_("Debit Account is mandatory"))
        
        if not self.credit_account:
            frappe.throw(_("Credit Account is mandatory"))
        
        if not self.cost_center:
            frappe.throw(_("Cost Center is mandatory"))
        
        if flt(self.net_total) <= 0 and flt(self.grand_total) <= 0:
            frappe.throw(_("Amount must be greater than zero"))
        
        if flt(self.net_total) <= 0:
            frappe.throw(_("Net Total must be greater than zero"))
        
        if flt(self.grand_total) <= 0:
            frappe.throw(_("Grand Total must be greater than zero"))
        
        # Validate taxes if present
        if self.taxes:
            for tax in self.taxes:
                if not tax.account_head:
                    frappe.throw(_("Account Head is mandatory for Tax row"))
                if flt(tax.tax_amount) < 0:
                    frappe.throw(_("Tax Amount cannot be negative"))
                if not tax.cost_center and not self.cost_center:
                    frappe.throw(_("Cost Center is mandatory for Tax row"))

    def make_gl_entry(self, cancel=0):
        gl_entries = []
        
        total_debit = 0
        total_credit = 0
        
        gl_entries.append(
            self.get_gl_dict({
                "account": self.debit_account,
                "debit": flt(self.amount, 2),
                "debit_in_account_currency": flt(self.amount, 2),
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "posting_date": self.posting_date,
                "company": self.company,
                "cost_center": self.cost_center,
                "party_type": self.party_type,
                "party": self.party,
                "against": self.credit_account,
                "remarks": _("Against POL Receive Invoice {0}").format(self.name)
            })
        )
        
        if self.taxes:
            for tax in self.taxes:
                if tax.tax_amount and flt(tax.tax_amount) > 0:
                    tax_amount = flt(tax.tax_amount, 2)
                    
                    if tax.add_deduct_tax == "Add":
                        gl_entries.append(
                            self.get_gl_dict({
                                "account": tax.account_head,
                                "debit": tax_amount,
                                "debit_in_account_currency": tax_amount,
                                "voucher_type": self.doctype,
                                "voucher_no": self.name,
                                "posting_date": self.posting_date,
                                "company": self.company,
                                "cost_center": tax.cost_center or self.cost_center,
                                "party_type": self.party_type,
                                "party": self.party,
                                "against": self.credit_account,
                                "remarks": _("Tax: {0}").format(tax.description or tax.account_head)
                            })
                        )
                        
                    elif tax.add_deduct_tax == "Deduct":
                        gl_entries.append(
                            self.get_gl_dict({
                                "account": tax.account_head,
                                "credit": tax_amount,
                                "credit_in_account_currency": tax_amount,
                                "voucher_type": self.doctype,
                                "voucher_no": self.name,
                                "posting_date": self.posting_date,
                                "company": self.company,
                                "cost_center": tax.cost_center or self.cost_center,
                                "party_type": self.party_type,
                                "party": self.party,
                                "against": self.debit_account,
                                "remarks": _("Tax Deduction: {0}").format(tax.description or tax.account_head)
                            })
                        )
        
        gl_entries.append(
            self.get_gl_dict({
                "account": self.credit_account,
                "credit": flt(self.amount_after_gst, 2),
                "credit_in_account_currency": flt(self.amount_after_gst, 2),
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "posting_date": self.posting_date,
                "company": self.company,
                "cost_center": self.cost_center,
                "party_type": self.party_type,
                "party": self.party,
                "against": ", ".join([self.debit_account] + [t.account_head for t in self.taxes if t.get("add_deduct_tax") == "Add" and t.tax_amount > 0]),
                "against_voucher": self.name,
                "against_voucher_type": self.doctype,
                "remarks": _("Payable against POL Receive Invoice {0}").format(self.name)
            })
        )
        
        if gl_entries:
            make_gl_entries(gl_entries, cancel=cancel, adv_adj=False)
            
        if not cancel:
            frappe.msgprint(
                _("GL Entries created successfully for POL Receive Invoice {0}").format(self.name),
                alert=True
            )

    def on_submit(self):
        """Submit - Create GL entries exactly like POL Receive"""
        self.validate_accounting_entries()
        self.make_gl_entry(cancel=0)

    def on_cancel(self):
        """Cancel - Reverse GL entries exactly like POL Receive"""
        self.make_gl_entry(cancel=1)
        self.db_set("status", "Cancelled")
