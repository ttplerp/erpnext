# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.controllers.accounts_controller import AccountsController

class OnlineOrderPayment(AccountsController):
    def validate(self):
        self.validate_data()

    def validate_data(self):
        total_amount = 0
        for a in self.items:
            a.total_price = flt(a.qty) * flt(a.price)
            total_amount += flt(a.total_price)
        self.total_amount = total_amount

    def on_submit(self):
        #self.create_stock_entry()
        self.make_gl_entry()
        self.update_order()

    def create_stock_entry(self):
        s = frappe.new_doc("Stock Entry")
        s.title = "online ordered by {}".format(self.desuup_name)
        s.branch = self.branch
        s.stock_entry_type = "Material Issue"
        s.posting_date = self.posting_date
        s.from_warehouse = self.warehouse

        for i in self.items:
            s.append("items", {
                "item_code": i.item_code,
                "s_warehouse": self.warehouse,
                "qty": i.qty,
                "cost_enter": self.cost_center
            })
        s.docstatus = 1
        s.save(ignore_permissions=True)
        self.db_set("stock_entry", s.name)

    def update_order(self):
        o = frappe.get_doc("Online Order", self.online_order)
        o.db_set("status", "Payment verified", update_modified=False)

    def make_gl_entry(self):
        from erpnext.accounts.general_ledger import make_gl_entries
        gl_entries = []

        income_account = frappe.db.get_value("Company", self.company, "online_sales_income")
        bank_account = frappe.db.get_value("Company", self.company, "online_bank_account")
        if not income_account:
            frappe.throw("Setup Online Sales Income Account in Accounts Settings")
        if not bank_account:
            frappe.throw("Setup Online Sales Bank Account in Accounts Settings")

        gl_entries.append(
            self.get_gl_dict({
                "account": bank_account,
                "debit": self.total_amount,
                "debit_in_account_currency": self.total_amount,
                "voucher_no": self.name,
                "voucher_type": self.doctype,
                "cost_center": self.cost_center,
                "business_activity": self.business_activity
            }, self.currency)
        )

        gl_entries.append(
            self.get_gl_dict({
                "account": income_account,
                "credit": self.total_amount,
                "credit_in_account_currency": self.total_amount,
                "voucher_no": self.name,
                "voucher_type": self.doctype,
                "business_activity": self.business_activity,
                "cost_center": self.cost_center
                }, self.currency)
            )
        make_gl_entries(gl_entries, cancel=(self.docstatus == 2),update_outstanding="Yes", merge_entries=False)

