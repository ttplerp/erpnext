# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, add_days, date_diff, nowdate
from frappe.utils.csvutils import UnicodeWriter

class UploadServiceList(Document):
	pass

@frappe.whitelist()
def get_template():
	if not frappe.has_permission("Service", "create"):
		raise frappe.PermissionError

	args = frappe.local.form_dict

	w = UnicodeWriter()
	w = add_header(w)

	# write out response as a type csv
	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Service"

def add_header(w):
	w.writerow(["Notes:"])
	w.writerow(["Please DO NOT change the template headings"])
	w.writerow([""])
	w.writerow(["Service Name", "Service Category", "Sub Category", "BSR Item", "BSR Code", "Uom", "Same Rate", "Cost", "Region1", "Rate1", "Region2", "Rate2", "Region3", "Rate3", "Region4", "Rate4"])

	return w

@frappe.whitelist()
def upload():
	if not frappe.has_permission("Service", "create"):
		raise frappe.PermissionError

	from frappe.utils.csvutils import read_csv_content_from_uploaded_file
	from frappe.modules import scrub

	rows = read_csv_content_from_uploaded_file()
	rows = filter(lambda x: x and any(x), rows)
	if not rows:
		msg = [_("Please select a csv file")]
		return {"messages": msg, "error": msg}

	#Columns located at 4th row
	columns = [scrub(f) for f in rows[2]]
	ret = []
	error = False

	from frappe.utils.csvutils import check_record, import_doc

	for i, row in enumerate(rows[3:]):
		if not row: continue
		row_idx = i + 3
		d = frappe._dict(zip(columns, row))
		try:
			ret.append("Row#{0}: {1}".format(i+1,d.service_name))
			if d.service_name:
				#ser = frappe.get_doc("Service", d.service_name)

				if frappe.db.exists("Service", {"item_name": d.service_name}):
					ret.append("Service already created for " + str(d.service_name))
					continue

				doc = frappe.new_doc("Service")
				doc.item_name = str(d.service_name)
				doc.item_group = d.service_category
				doc.item_sub_group = d.sub_category
				doc.bsr_service_item = d.bsr_item
				doc.bsr_item_code = d.bsr_code
				doc.stock_uom = d.uom
				doc.same_rate = d.same_rate
				doc.cost = flt(d.cost)
				if d.region1:
					doc.append("bsr_detail_item",{"region": d.region1, "rate": flt(d.rate1)})
				if d.region2:
					doc.append("bsr_detail_item",{"region": d.region2, "rate": flt(d.rate2)})
				if d.region3:
					doc.append("bsr_detail_item",{"region": d.region3, "rate": flt(d.rate3)})
				if d.region4:
					doc.append("bsr_detail_item",{"region": d.region4, "rate": flt(d.rate4)})
				doc.insert()
			else:
				frappe.throw("No service record on row " + str(row_idx))

			ret.append("Service created for " + str(d.service_name))
		except Exception as e:
			frappe.db.rollback()
			error = True
			ret.append('Error for row (#%d) ' % (row_idx))
			ret.append(str(frappe.get_traceback()))
			frappe.errprint(frappe.get_traceback())

	return {"messages": ret, "error": error} 
