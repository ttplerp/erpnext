# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, qb
from frappe.utils import flt, cint
from erpnext.custom_utils import check_future_date
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from frappe.utils import money_in_words, cstr, flt, formatdate, cint, now_datetime
from erpnext.controllers.stock_controller import StockController
from erpnext.accounts.general_ledger import (
    make_gl_entries,
    merge_similar_entries,
)
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

from erpnext.accounts.party import get_party_account


class POLReceive(StockController):
    def validate(self):
        check_future_date(self.posting_date)
        self.calculate_km_diff()
        self.validate_data()
        validate_workflow_states(self)
        if self.workflow_state != "Approved":
            notify_workflow_states(self)
        # self.balance_check()

    def on_submit(self):
        if self.direct_consumption == 0 and self.receive_in_barrel == 1:
            self.update_stock_ledger()
            self.repost_future_sle_and_gle()
        self.update_pol_expense()
        self.make_pol_entry()
        self.post_journal_entry()
        notify_workflow_states(self)
        # self.make_gl_entries()

    def before_cancel(self):
        if self.direct_consumption == 0 and self.receive_in_barrel == 1:
            self.update_stock_ledger()
            self.cancel_je()
        self.delete_pol_entry()

    def cancel_je(self):
        if self.journal_entry:
            je = frappe.get_doc("Journal Entry", self.journal_entry)
            if (
                frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
                == 1
            ):
                je.flags.ignore_permissions = 1
                je.cancel()
            elif (
                frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
                == 0
            ):
                for a in je.accounts:
                    child_doc = frappe.get_doc("Journal Entry Account", a.name)
                    child_doc.db_set("reference_type", None)
                    child_doc.db_set("reference_name", None)
                frappe.db.commit()
                frappe.db.sql(
                    """
					delete from `tabJournal Entry` where name = '{}'
				""".format(
                        self.journal_entry
                    )
                )
                frappe.db.sql(
                    """
					delete from `tabJournal Entry Account` where parent = '{}'
				""".format(
                        self.journal_entry
                    )
                )

    def on_cancel(self):
        self.update_pol_expense()
        self.delete_pol_entry()
        # notify_workflow_states(self)
        if self.direct_consumption == 0 and self.receive_in_barrel == 1:
            self.update_stock_ledger()
            self.repost_future_sle_and_gle()
        # self.make_gl_entries()

    def update_stock_ledger(self):
        sl_entries = []
        # finished_item_row = self.get_finished_item_row()

        # make sl entries for source warehouse first
        # self.get_sle_for_source_warehouse(sl_entries, finished_item_row)

        # SLE for target warehouse
        self.get_sle_for_target_warehouse(sl_entries)

        # reverse sl entries if cancel
        if self.docstatus == 2:
            sl_entries.reverse()

        self.make_sl_entries(sl_entries)

    def get_sle_for_target_warehouse(self, sl_entries):
        if cstr(self.warehouse):
            sle = self.get_sl_entries(
                {"item_code": self.pol_type, "name": self.name},
                {
                    "warehouse": cstr(self.warehouse),
                    "actual_qty": flt(self.qty),
                    "incoming_rate": flt(self.rate),
                    "valuation_rate": flt(self.rate),
                },
            )

            sl_entries.append(sle)

    # def balance_check(self):
    # 	total_balance = 0
    # 	for row in self.items:
    # 		total_balance = flt(total_balance) + flt(row.balance_amount)
    # 	if total_balance < self.total_amount :
    # 		frappe.throw("<b>Payable Amount({})</b> cannot be greater than <b>Total Advance Balance({})</b>".format(self.total_amount,total_balance))

    def post_journal_entry(self):
        if not self.total_amount:
            frappe.throw(_("Amount should be greater than zero"))
        credit_account = frappe.get_value(
            "Company", self.company, "default_bank_account"
        )
        if self.settle_imprest_advance == 1:
            credit_account = frappe.get_value(
                "Company", self.company, "imprest_advance_account"
            )
        # debit_account = frappe.db.get_value(
        #     "Equipment Category", self.equipment_category, "r_m_expense_account"
        # )
        # if self.direct_consumption:
        enable_pol_receive_acc = pol_receive_account = pol_advance_account = None
        if self.equipment:
            (
                enable_pol_receive_acc,
                pol_receive_account,
                pol_advance_account,
            ) = frappe.db.get_value(
                "Equipment Category",
                self.equipment_category,
                [
                    "enable_pol_receive_account",
                    "pol_receive_account",
                    "pol_advance_account",
                ],
            )
        if (
            enable_pol_receive_acc == 1
            and frappe.db.get_value("Equipment", self.equipment, "is_container") == 1
        ):
            debit_account = pol_receive_account
        else:
            debit_account = pol_advance_account
            # debit_account = frappe.db.get_value(
            #     "Equipment Category", self.equipment_category, "pol_advance_account"
            # )
        if not debit_account and self.receive_in_barrel == 1:
            debit_account = frappe.db.get_value("Warehouse", self.warehouse, "account")

        # Posting Journal Entry
        je = frappe.new_doc("Journal Entry")
        je.flags.ignore_permissions = 1
        accounts = []
        if self.settle_imprest_advance == 0 or not self.settle_imprest_advance:
            accounts.append(
                {
                    "account": credit_account,
                    "credit_in_account_currency": flt(self.total_amount, 2),
                    "credit": flt(self.total_amount, 2),
                    "cost_center": self.cost_center,
                    "reference_type": "POL Receive",
                    "reference_name": self.name,
                    "business_activity": get_default_ba,
                }
            )
        else:
            accounts.append(
                {
                    "account": credit_account,
                    "credit_in_account_currency": flt(self.total_amount, 2),
                    "credit": flt(self.total_amount, 2),
                    "cost_center": self.cost_center,
                    "reference_type": "POL Receive",
                    "reference_name": self.name,
                    "party_type": "Employee",
                    "party": self.party,
                    "business_activity": get_default_ba,
                }
            )
        accounts.append(
            {
                "account": debit_account,
                "debit_in_account_currency": flt(self.total_amount, 2),
                "debit": flt(self.total_amount, 2),
                "cost_center": self.cost_center,
                "business_activity": get_default_ba,
            }
        )

        je.update(
            {
                "doctype": "Journal Entry",
                "voucher_type": "Journal Entry",
                "naming_series": "Bank Payment Voucher"
                if self.settle_imprest_advance == 0
                else "Journal Voucher",
                "title": "POL Receive - " + self.equipment
                if self.receive_in_barrel == 0
                else "",
                "user_remark": "Note: " + "POL Receive - " + self.equipment
                if self.receive_in_barrel == 0
                else "",
                "posting_date": self.posting_date,
                "company": self.company,
                "total_amount_in_words": money_in_words(self.total_amount),
                "branch": self.branch,
                "accounts": accounts,
                "total_debit": flt(self.total_amount, 2),
                "total_credit": flt(self.total_amount, 2),
                "settle_project_imprest": self.settle_imprest_advance,
            }
        )
        # frappe.throw('{}'.format(accounts))
        je.insert()
        # Set a reference to the claim journal entry
        self.db_set("journal_entry", je.name)
        self.db_set(
            "journal_entry_status",
            "Forwarded to accounts for processing payment on {0}".format(
                now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            ),
        )
        frappe.msgprint(
            _("{} posted to accounts").format(
                frappe.get_desk_link("Journal Entry", je.name)
            )
        )
        # frappe.throw('Here!')

    def make_gl_entries(self):
        if cint(self.out_sourced) == 0:
            return

        gl_entries = []
        self.make_supplier_gl_entry(gl_entries)
        self.make_expense_gl_entry(gl_entries)
        gl_entries = merge_similar_entries(gl_entries)
        make_gl_entries(gl_entries, update_outstanding="No", cancel=self.docstatus == 2)

    def make_supplier_gl_entry(self, gl_entries):
        if flt(self.total_amount) > 0:
            credit_account = get_party_account("Supplier", self.supplier, self.company)
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": credit_account,
                        "credit": self.total_amount,
                        "credit_in_account_currency": self.total_amount,
                        "against_voucher": self.name,
                        "party_type": "Supplier",
                        "party": self.supplier,
                        "against_voucher_type": self.doctype,
                        "cost_center": self.cost_center,
                        "voucher_type": self.doctype,
                        "voucher_no": self.name,
                    },
                    self.currency,
                )
            )

    def make_expense_gl_entry(self, gl_entries):
        if flt(self.total_amount) > 0:
            expense_account = frappe.db.get_value(
                "Company", self.company, "pol_expense_account"
            )
            gl_entries.append(
                self.get_gl_dict(
                    {
                        "account": expense_account,
                        "debit": self.total_amount,
                        "debit_in_account_currency": self.total_amount,
                        "against_voucher": self.name,
                        "party_type": "Supplier",
                        "party": frappe.db.get_value(
                            "Equipment", self.equipment, "supplier"
                        ),
                        "against_voucher_type": self.doctype,
                        "cost_center": self.cost_center,
                        "voucher_type": self.doctype,
                        "voucher_no": self.name,
                    },
                    self.currency,
                )
            )

    def update_pol_expense(self):
        if self.docstatus == 2:
            for item in self.items:
                doc = frappe.get_doc("POL Expense", {"name": item.pol_expense})
                doc.adjusted_amount = flt(doc.adjusted_amount) - flt(
                    item.allocated_amount
                )
                doc.balance_amount = flt(doc.amount) - flt(doc.adjusted_amount)
                doc.save(ignore_permissions=True)
            return
        for item in self.items:
            doc = frappe.get_doc("POL Expense", {"name": item.pol_expense})
            doc.balance_amount = flt(item.balance_amount) - flt(item.allocated_amount)
            doc.adjusted_amount = flt(doc.adjusted_amount) + flt(item.allocated_amount)
            doc.save(ignore_permissions=True)

    @frappe.whitelist()
    def get_previous_km_reading(self):
        previous_km_reading = frappe.db.sql(
            """
						select cur_km_reading from `tabPOL Receive` where docstatus = 1 
						and equipment = '{}' and uom = '{}'
						order by posting_date desc, posting_time desc
						limit 1
						""".format(
                self.equipment, self.uom
            )
        )
        previous_km_reading_pol_issue = frappe.db.sql(
            """
				select cur_km_reading
				from `tabPOL Issue` p inner join `tabPOL Issue Items` pi on p.name = pi.parent	
				where p.docstatus = 1 and pi.equipment = '{}'
				and pi.uom = '{}' 
				order by p.posting_date desc, p.posting_time desc
				limit 1
			""".format(
                self.equipment, self.uom
            )
        )
        if not previous_km_reading and previous_km_reading_pol_issue:
            previous_km_reading = previous_km_reading_pol_issue
        elif previous_km_reading and previous_km_reading_pol_issue:
            if flt(previous_km_reading[0][0]) < previous_km_reading_pol_issue[0][0]:
                previous_km_reading = previous_km_reading_pol_issue

        pv_km = 0
        if not previous_km_reading:
            pv_km = frappe.db.get_value(
                "Equipment", self.equipment, "initial_km_reading"
            )
        else:
            pv_km = previous_km_reading[0][0]
        self.previous_km = pv_km
        return pv_km

    def calculate_km_diff(self):
        if cint(self.hired_equipment) == 1:
            return
        if cint(self.direct_consumption) == 0:
            return
        if not self.uom:
            self.uom = frappe.db.get_value("Equipment", self.equipment, "reading_uom")
        if not self.uom:
            self.uom = frappe.db.get_value(
                "Equipment Type", self.equipment_type, "reading_uom"
            )
        
        pv_km = self.get_previous_km_reading()
        # Commentted by Dawa Tshering on 20/11/2023
        # if flt(pv_km) >= flt(self.cur_km_reading):
        #     frappe.throw(
        #         "Current KM/Hr Reading cannot be less than Previous KM/Hr Reading({}) for Equipment Number <b>{}</b>".format(
        #             pv_km, self.equipment
        #         )
        #     )
        # self.km_difference = flt(self.cur_km_reading) - flt(pv_km)
        # if self.uom == "Hour":
        #     self.mileage = self.qty / flt(self.km_difference)
        # else:
        #     self.mileage = flt(self.km_difference) / self.qty

        # Commentted by Dawa Tshering on 20/11/2023
        if flt(pv_km) >= flt(self.cur_km_reading):
            frappe.throw(
                "Current KM/Hr Reading cannot be less than Previous KM/Hr Reading({}) for Equipment Number <b>{}</b>".format(
                    pv_km, self.equipment
                )
            )
        self.km_difference = flt(self.cur_km_reading) - flt(pv_km)
        if self.uom == "Hour":
            self.mileage = self.qty / flt(self.km_difference)
        else:
            self.mileage = flt(self.km_difference) / self.qty

    def validate_data(self):
        # if not self.fuelbook_branch:
        # 	frappe.throw("Fuelbook Branch are mandatory")

        if flt(self.qty) <= 0 or flt(self.rate) <= 0:
            frappe.throw("Quantity and Rate should be greater than 0")

        if not self.equipment_category and self.receive_in_barrel == 0:
            frappe.throw("Vehicle Category Missing")

    @frappe.whitelist()
    def populate_child_table(self):
        self.calculate_km_diff()
        pol_exp = qb.DocType("POL Expense")
        je = qb.DocType("Journal Entry")
        data = []
        if not self.equipment:
            frappe.throw("Either equipment is missing")
        data = (
            qb.from_(pol_exp)
            .select(pol_exp.name, pol_exp.amount, pol_exp.balance_amount)
            .where(
                (pol_exp.docstatus == 1)
                & (pol_exp.balance_amount > 0)
                & (pol_exp.fuel_book == self.fuelbook)
            )
            .orderby(pol_exp.entry_date, order=qb.desc)
        ).run(as_dict=True)
        if not data:
            frappe.throw(
                "NO POL Expense Found against Equipment {}".format(self.equipment)
            )
        self.set("items", [])
        allocated_amount = self.total_amount
        total_amount_adjusted = 0
        for d in data:
            if cint(d.is_opening) == 0:
                row = self.append("items", {})
                row.pol_expense = d.name
                row.amount = d.amount
                row.balance_amount = d.balance_amount
                if row.balance_amount >= allocated_amount:
                    row.allocated_amount = allocated_amount
                    total_amount_adjusted += flt(row.allocated_amount)
                    allocated_amount = 0
                elif row.balance_amount < allocated_amount:
                    row.allocated_amount = row.balance_amount
                    total_amount_adjusted += flt(row.allocated_amount)
                    allocated_amount = flt(allocated_amount) - flt(row.balance_amount)
                row.balance = flt(row.balance_amount) - flt(row.allocated_amount)
            else:
                row = self.append("items", {})
                row.pol_expense = d.name
                row.amount = d.amount
                row.balance_amount = d.balance_amount
                if row.balance_amount >= allocated_amount:
                    row.allocated_amount = allocated_amount
                    total_amount_adjusted += flt(row.allocated_amount)
                    allocated_amount = 0
                elif row.balance_amount < allocated_amount:
                    row.allocated_amount = row.balance_amount
                    total_amount_adjusted += flt(row.allocated_amount)
                    allocated_amount = flt(allocated_amount) - flt(row.balance_amount)
                row.balance = flt(row.balance_amount) - flt(row.allocated_amount)

    def make_pol_entry(self):
        container = frappe.db.get_value(
            "Equipment Type", self.equipment_type, "is_container"
        )
        if (
            not self.direct_consumption
            and not container
            and self.receive_in_barrel == 0
        ):
            frappe.throw(
                "Equipment {} is not a container".format(frappe.bold(self.equipment))
            )

        if self.direct_consumption:
            con1 = frappe.new_doc("POL Entry")
            con1.flags.ignore_permissions = 1
            con1.equipment = self.equipment
            con1.pol_type = self.pol_type
            con1.branch = self.branch
            con1.posting_date = self.posting_date
            con1.posting_time = self.posting_time
            con1.qty = self.qty
            con1.reference_type = self.doctype
            con1.reference = self.name
            con1.type = "Receive"
            con1.is_opening = 0
            con1.cost_center = self.cost_center
            con1.current_km = self.cur_km_reading
            con1.mileage = self.mileage
            con1.uom = self.uom
            con1.submit()
        elif container:
            con = frappe.new_doc("POL Entry")
            con.flags.ignore_permissions = 1
            con.equipment = self.equipment
            con.pol_type = self.pol_type
            con.branch = self.branch
            con.posting_date = self.posting_date
            con.posting_time = self.posting_time
            con.qty = self.qty
            con.reference_type = self.doctype
            con.reference = self.name
            con.is_opening = 0
            con.uom = self.uom
            con.cost_center = self.cost_center
            con.type = "Stock"
            con.submit()

            # if container:
            # 	con2 = frappe.new_doc("POL Entry")
            # 	con2.flags.ignore_permissions = 1
            # 	con2.equipment = self.equipment
            # 	con2.pol_type = self.pol_type
            # 	con2.branch = self.branch
            # 	con2.date = self.posting_date
            # 	con2.posting_time = self.posting_time
            # 	con2.qty = self.qty
            # 	con2.reference_type = self.doctype
            # 	con2.reference_name = self.name
            # 	con2.type = "Issue"
            # 	con2.is_opening = 0
            # 	con2.cost_center = self.cost_center
            # 	con2.submit()

    def delete_pol_entry(self):
        frappe.db.sql("delete from `tabPOL Entry` where reference = %s", self.name)


# query permission
def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user
    user_roles = frappe.get_roles(user)

    if user == "Administrator" or "System Manager" in user_roles:
        return

    return """(
		`tabPOL Receive`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabPOL Receive`.branch
			and e.user_id = '{user}')
		or
		exists(select 1
			from `tabEmployee` e, `tabAssign Branch` ab, `tabBranch Item` bi
			where e.user_id = '{user}'
			and ab.employee = e.name
			and bi.parent = ab.name
			and bi.branch = `tabPOL Receive`.branch)
	)""".format(
        user=user
    )
