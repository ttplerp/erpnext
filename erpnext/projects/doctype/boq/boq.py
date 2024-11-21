from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname
from frappe.utils import cstr, flt, getdate, today, nowdate, now_datetime
from datetime import date
from erpnext.accounts.party import get_party_account

class BOQ(Document):	
	def validate(self):
		self.set_defaults()
		self.validate_defaults()
	
	def on_submit(self):
		self.update_project_value()
		self.project_boq_item_entry()

	def on_cancel(self):
		self.update_project_value(cancel=True)
		self.project_boq_item_entry(cancel=True)

	def on_update_after_submit(self):
		self.project_boq_item_entry()

	# def calculate_quantity(self): 
	# 	for d in self.boq_item:
	# 		d.quantity = d.no * d.length * d.breath * d.height * d.coefficient

	def project_boq_item_entry(self, cancel=False):
		if cancel:
			frappe.db.sql("delete from `tabProject BOQ Item` where parent='{project}' and boq_name = '{boq_name}'".format(project=self.project, boq_name=self.name))

		else:
			if not frappe.db.exists("Project BOQ Item", {"parent": self.project, "boq_name": self.name}):
				doc = frappe.get_doc("Project", self.project)
				row = doc.append("project_boq_item", {})
				row.boq_name            = self.name
				row.boq_date            = self.boq_date
				row.amount              = flt(self.total_amount)
				row.price_adjustment    = flt(self.price_adjustment)
				row.total_amount        = flt(self.total_amount)+flt(self.price_adjustment)
				# row.received_amount     = flt(self.received_amount)
				# row.paid_amount         = flt(self.paid_amount)
				# row.balance_amount      = flt(self.balance_amount)
				row.save(ignore_permissions=True)
			else:
				row = frappe.get_doc("Project BOQ Item", {"parent": self.project, "boq_name": self.name})
				row.boq_date            = self.boq_date
				row.amount              = flt(self.total_amount)
				row.price_adjustment    = flt(self.price_adjustment)
				row.total_amount        = flt(self.total_amount)+flt(self.price_adjustment)
				# row.received_amount     = flt(self.received_amount)
				# row.paid_amount         = flt(self.paid_amount)
				# row.balance_amount      = flt(self.balance_amount)
				row.save(ignore_permissions=True)

	def validate_defaults(self):
		if not all((self.project, self.branch, self.cost_center)):
			frappe.throw("Either one of them is not set <b>Project, Branch or Cost Center</b> cannot be null.")

		if flt(self.total_amount,0) <= 0:
			frappe.throw(_("Invalid total amount."), title="Invalid Data")

	def set_defaults(self):
		self.total_amount = self.price_adjustment = self.claimed_amount = self.total_unclaimed_amount = 0.0
		for item in self.boq_item:
			item.claimed_quantity = item.claimed_amount = item.quantity_before_subcontract = item.quantity_after_subcontract = 0.0 
			item.amount 						= flt(item.quantity) * flt(item.rate)
			self.total_amount 					+= flt(item.amount)
			item.unclaimed_quantity 			= flt(item.quantity)
			item.quantity_before_subcontract 	= flt(item.quantity)
			item.quantity_after_subcontract 	= flt(item.quantity)
			item.unclaimed_amount 				= flt(item.amount)
			self.total_unclaimed_amount 		+= flt(item.unclaimed_amount)
			
			if flt(item.amount) < 0:
				frappe.throw(_("Row#{0} : Invalid amount."), title="Invalid Data")
		
		# Defaults
		base_project = frappe.get_doc("Project", self.project)
		self.party_type = base_project.party_type
		self.party = base_project.party
		
		if base_project.status in ('Completed', 'Cancelled'):
			frappe.throw(_("Operation not permitted on already {0} Project.").format(base_project.status), title="BOQ: Invalid Operation")
		
		if not self.branch:
			self.branch = base_project.branch
		
		if not self.cost_center:
			self.cost_center = base_project.cost_center
		
		if not self.boq_date:
			self.boq_date = date.today()

	def update_project_value(self, cancel=False):
		if self.total_amount:
			pro_doc = frappe.get_doc("Project", self.project)
			pro_doc.flags.dont_sync_tasks = True
			pro_doc.boq_value = flt(pro_doc.boq_value)+(-1*(self.total_amount) if self.docstatus==2 else flt(self.total_amount))
			pro_doc.save(ignore_permissions = True)

@frappe.whitelist()
def make_boq_adjustment(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.total_amount = 0.0
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "BOQ Adjustment",
			"field_map": {
					"name": "boq"
			},
			"postprocess": update_master
		},

		"BOQ Item": {
			"doctype": "BOQ Adjustment Item",
			"field_map": {
				"bsr_code": "bsr_code",
				"quantity": "adjustment_quantity",
				"amount": "adjustment_amount",
			},
		}
	}, target_doc)

	return doclist
	
@frappe.whitelist()
def make_boq_substitution(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.total_amount = 0.0

	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "BOQ Substitution",
			"field_map": {
					"name": "boq"
			},
			"postprocess": update_master
		}

	}, target_doc, ignore_child_tables=True)

	return doclist

@frappe.whitelist()
def make_additional_boq(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.total_amount = 0.0
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "BOQ Addition",
			"field_map": {
					"name": "boq"
			},
			"postprocess": update_master
		}
	}, target_doc, ignore_child_tables=True)
	return doclist


@frappe.whitelist()
def make_direct_invoice(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.invoice_type = "Direct Invoice"
		target_doc.check_all = 1
			
	def update_item(source_doc, target_doc, source_parent):
		target_doc.act_quantity = flt(target_doc.invoice_quantity)
		target_doc.act_rate     = flt(target_doc.invoice_rate)
		target_doc.act_amount   = flt(target_doc.invoice_amount)
		target_doc.original_rate= flt(target_doc.invoice_rate)
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Project Invoice",
			"field_map": {
					"project": "project"
			},
			"postprocess": update_master
		},

		"BOQ Item": {
			"doctype": "Project Invoice BOQ",
			"field_map": {
					"name": "boq_item_name",
					"balance_quantity": "invoice_quantity",
					"balance_amount": "invoice_amount",
					"quantity": "original_quantity",
					"amount": "original_amount"
			},
			"postprocess": update_item
		}
	}, target_doc)

	return doclist

# Added by Dawa Tshering on 14/11/2024
@frappe.whitelist()
def make_boq_subcontract(source_name, target_doc=None):
	item_details = get_item_details(source_name)
	def set_missing_values(source, target):
		target.party_type = "Supplier" if source.party_type == "Customer" else None
		target.party = None
		target.set(
			"boq_item",
			[d for d in item_details]
		)

	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Subcontract"
		}
	}, target_doc, set_missing_values)

	return doclist

def get_item_details(doc_name):
	res = frappe.db.sql(
		"""
		select 
			t2.bsr_code, t2.uom, t2.description, t2.rate, t2.quantity_after_subcontract as total_quantity, t2.no, t2.length, t2.breath, t2.height, t2.coefficient
		from `tabBOQ` t1, `tabBOQ Item` t2
		where t1.name = t2.parent
		and t1.docstatus = 1
		and t1.name = %s
		and t2.quantity_after_subcontract > 0
		order by t2.bsr_code asc
		""", (doc_name), as_dict=True
	)
	for a in res:
		a['boq_quantity'] = a.total_quantity
		a['quantity'] = a.total_quantity
		a['unclaimed_quantity'] = a.total_quantity
		a['boq_rate'] = a.rate
		a['amount'] = flt(a.rate) * flt(a.total_quantity)
		a['boq_amount'] = flt(a.rate) * flt(a.total_quantity)
		a['unclaimed_amount'] = flt(a.rate) * flt(a.total_quantity)
	return res

@frappe.whitelist()
def make_project_ivoice(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.invoice_title = str(target_doc.project) + "(Project Invoice)"
		target_doc.check_all_mb = 1
		target_doc.debit_credit_account = get_party_account(source_doc.party_type, source_doc.party, source_doc.company)
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Project Invoice",
			"field_map": {
					"project": "project"
			},
			"postprocess": update_master
		}
	}, target_doc)

	return doclist


@frappe.whitelist()
def make_book_entry(source_name, target_doc=None):
	def update_master(source_doc, target_doc, source_parent):
		target_doc.check_all = 1

	def update_item(source_doc, target_doc, source_parent):
		target_doc.act_quantity  = flt(target_doc.entry_quantity)
		target_doc.act_rate      = flt(target_doc.entry_rate)
		target_doc.act_amount    = flt(target_doc.entry_amount)
		target_doc.original_rate = flt(target_doc.entry_rate)
			
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "MB Entry",
			"field_map": {
					"project": "project"
			},
			"postprocess": update_master
		},

		"BOQ Item": {
			"doctype": "MB Entry BOQ",
			"field_map": {
					"bsr_code": "bsr_code",
					"no": "no",
						"length": "length",
						"breath": "breath",
						"height": "height",
						"unclaimed_quantity": "entry_quantity",
						"rate": "entry_rate",
						"unclaimed_amount": "entry_amount",
						"quantity": "original_quantity",
						"amount": "original_amount"
			},
			"postprocess": update_item
		}
	}, target_doc)

	return doclist

@frappe.whitelist()
def make_rm(source_name, target_doc=None, args=None):
	from frappe.model.mapper import get_mapped_doc
	# if args is None:
	# 	args = {}
	# if isinstance(args, str):
	# 	args = json.loads(args)

	def post_process(source, target):
		target.branch = frappe.flags.args.branch
		target.cost_center = frappe.flags.args.cost_center
		target.child_ref = frappe.flags.args.child_ref
		target.bsr_code = frappe.flags.args.bsr_code
		target.description = frappe.flags.args.description
		target.uom = frappe.flags.args.uom
		target.rate = frappe.flags.args.rate
		target.entry_quantity = frappe.flags.args.quantity
		target.amount = frappe.flags.args.amount
		# set_missing_values(source, target_doc)

	# def select_item(d):
	#	 filtered_items = args.get("filtered_children", [])
	#	 child_filter = d.name in filtered_items if filtered_items else True

	#	 return d.ordered_qty < d.stock_qty and child_filter

	doclist = get_mapped_doc(
		"BOQ",
		source_name,
		{
			"BOQ": {
				"doctype": "Record Of Measurement",
			}
		},
		target_doc,
		post_process,
	)

	return doclist

@frappe.whitelist()
def make_boq_advance(source_name, target_doc=None):
	doclist = get_mapped_doc("BOQ", source_name, {
		"BOQ": {
			"doctype": "Project Advance",
			"field_map":{
				"project": "project",
				"party_type": "party_type",
				"party": "party",
				"party_address": "party_address"
			},
		}
	}, target_doc)
	return doclist
