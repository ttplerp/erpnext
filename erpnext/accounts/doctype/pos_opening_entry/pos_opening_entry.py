# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import cint, get_link_to_form

from erpnext.controllers.status_updater import StatusUpdater


class POSOpeningEntry(StatusUpdater):
	def validate(self):
		self.validate_pos_profile_and_cashier()
		self.validate_payment_method_account()
		self.validate_duplicate_opening_entry()
		self.set_status()

	def validate_pos_profile_and_cashier(self):
		if self.company != frappe.db.get_value("POS Profile", self.pos_profile, "company"):
			frappe.throw(
				_("POS Profile {} does not belongs to company {}").format(self.pos_profile, self.company)
			)

		if not cint(frappe.db.get_value("User", self.user, "enabled")):
			frappe.throw(_("User {} is disabled. Please select valid user/cashier").format(self.user))

	def validate_payment_method_account(self):
		invalid_modes = []
		for d in self.balance_details:
			if d.mode_of_payment:
				account = frappe.db.get_value(
					"Mode of Payment Account",
					{"parent": d.mode_of_payment, "company": self.company},
					"default_account",
				)
				if not account:
					invalid_modes.append(get_link_to_form("Mode of Payment", d.mode_of_payment))

		if invalid_modes:
			if invalid_modes == 1:
				msg = _("Please set default Cash or Bank account in Mode of Payment {}")
			else:
				msg = _("Please set default Cash or Bank account in Mode of Payments {}")
			frappe.throw(msg.format(", ".join(invalid_modes)), title=_("Missing Account"))

	def validate_duplicate_opening_entry(self):
		# for d in frappe.db.get_all("POS Opening Entry", {"user": self.user, "pos_profile": self.pos_profile, "posting_date": self.posting_date, "status": "Open", "docstatus":1, "name": ("!=", self.name)}):
		for d in frappe.db.get_all("POS Opening Entry", {"pos_profile": self.pos_profile, "posting_date": self.posting_date, "docstatus": ("<", 2), "name": ("!=", self.name)}):
			frappe.throw(
				_("POS Opening Entry already created for <b>{}</b>, cannot create again. Reference <b>{}</b>").format(self.posting_date, d.name)
			)

	def on_submit(self):
		self.set_status(update=True)

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles: 
		return

	return """(
		`tabPOS Opening Entry`.owner = '{user}'
		or
		exists(select 1
			from `tabPOS Profile User` as e, `tabPOS Profile` p
			where e.parent = p.name
			and p.name = `tabPOS Opening Entry`.pos_profile
			and e.user = '{user}')
	)""".format(user=user)