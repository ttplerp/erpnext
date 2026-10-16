# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class DeploymentEntry(Document):
    def on_submit(self):
        self.update_points()

    def update_points(self):
        if flt(self.heart_points) > 0 and self.points_updated == 0:
            d = frappe.get_doc("Desuup", self.desuup)
            new_point = flt(d.heart_points) + flt(self.heart_points)
            self.db_set("points_updated", 1, update_modified=False)
            d.db_set("heart_points", new_point, update_modified=False )

    def on_cancel(self):
        self.cancel_points()

    def cancel_points(self):
        if flt(self.heart_points) > 0 and self.points_updated == 1:
            d = frappe.get_doc("Desuup", self.desuup)
            new_point = flt(d.heart_points) - flt(self.heart_points)
            d.db_set("heart_points", new_point, update_modified=False )
