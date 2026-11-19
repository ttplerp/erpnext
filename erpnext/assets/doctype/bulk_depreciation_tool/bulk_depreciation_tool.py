# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, today

class BulkDepreciationTool(Document):
    def validate(self):
        self.validate_dates()
        self.validate_company()

    def validate_dates(self):
        if self.from_date and self.to_date:
            if getdate(self.from_date) > getdate(self.to_date):
                frappe.throw(_("From Date cannot be after To Date"))

    def validate_company(self):
        if not self.company:
            frappe.throw(_("Company is required"))

    @frappe.whitelist()
    def fetch_pending_assets(self):
        """Fetch all assets with pending depreciation schedules"""
        if not self.from_date or not self.to_date:
            frappe.msgprint(_("Please select From Date and To Date"))
            return 0

        if not self.company:
            frappe.msgprint(_("Please select Company"))
            return 0

        # Clear existing entries
        self.set('assets', [])
        
        try:
            # Get assets with pending depreciation
            assets = frappe.db.sql("""
                SELECT 
                    a.name,
                    a.asset_name,
                    a.company,
                    a.status,
                    a.gross_purchase_amount,
                    a.branch,
                    COUNT(ds.name) as pending_schedules,
                    SUM(ds.depreciation_amount) as total_pending_amount,
                    GROUP_CONCAT(ds.schedule_date SEPARATOR ', ') as schedule_dates
                FROM 
                    `tabAsset` a
                INNER JOIN 
                    `tabDepreciation Schedule` ds ON a.name = ds.parent
                WHERE 
                    a.docstatus = 1
                    AND a.calculate_depreciation = 1
                    AND a.status IN ('Submitted', 'Partially Depreciated')
                    AND a.company = %s
                    AND ds.schedule_date BETWEEN %s AND %s
                    AND (ds.journal_entry IS NULL OR ds.journal_entry = '')
                GROUP BY 
                    a.name
                ORDER BY 
                    a.name
            """, (self.company, self.from_date, self.to_date), as_dict=1)

            if assets:
                for asset in assets:
                    self.append('assets', {
                        'asset': asset.name,
                        'asset_name': asset.asset_name,
                        'company': asset.company,
                        'status': asset.status,
                        'gross_purchase_amount': asset.gross_purchase_amount,
                        'pending_schedules': asset.pending_schedules,
                        'total_pending_amount': asset.total_pending_amount,
                        'schedule_dates': asset.schedule_dates[:200] if asset.schedule_dates else '',
                        'branch': asset.branch or 'No Branch Set'
                    })

            self.total_assets = len(assets)
            self.total_pending_amount = sum(flt(a.total_pending_amount) for a in assets) if assets else 0

        except Exception as e:
            error_msg = f"Error in fetch_pending_assets: {str(e)}"
            frappe.log_error(error_msg, "Bulk Depreciation Error")
            frappe.throw(_(f"Error fetching assets: {str(e)}"))

        return self.total_assets

    @frappe.whitelist()
    def process_depreciation(self):
        """Process all pending depreciation entries"""
        if not self.assets:
            frappe.throw(_("No assets found for depreciation"))

        # Get or create default branch for this company
        default_branch = self.get_or_create_branch()
        success_count = 0
        failed_count = 0
        errors = []

        for asset_row in self.assets:
            try:
                # STEP 1: Check if asset has branch, if not, set it
                asset_doc = frappe.get_doc("Asset", asset_row.asset)
                
                if not asset_doc.branch:
                    # Set the default branch on the asset
                    frappe.db.set_value("Asset", asset_row.asset, "branch", default_branch)
                    frappe.db.commit()
                    asset_doc.reload()
                    frappe.msgprint(_(f"✓ Set branch '{default_branch}' for asset {asset_row.asset_name}"))
                
                # Get pending schedules for this asset
                schedules = frappe.db.sql("""
                    SELECT name, schedule_date, depreciation_amount
                    FROM `tabDepreciation Schedule`
                    WHERE parent = %s
                        AND schedule_date BETWEEN %s AND %s
                        AND (journal_entry IS NULL OR journal_entry = '')
                    ORDER BY schedule_date
                """, (asset_row.asset, self.from_date, self.to_date), as_dict=1)

                if not schedules:
                    continue

                for schedule in schedules:
                    try:
                        # STEP 2: Call the original make_depreciation_entry
                        # Now asset has a branch, so it will work!
                        from erpnext.assets.doctype.asset.depreciation import make_depreciation_entry
                        make_depreciation_entry(asset_row.asset, schedule.schedule_date)
                        success_count += 1
                        frappe.db.commit()
                        
                    except Exception as e:
                        failed_count += 1
                        error_msg = f"Asset: {asset_row.asset_name}, Date: {schedule.schedule_date} - {str(e)}"
                        errors.append(error_msg)
                        frappe.db.rollback()
                        frappe.log_error(error_msg, "Bulk Depreciation Error")

            except Exception as e:
                failed_count += 1
                error_msg = f"Asset: {asset_row.asset_name} - {str(e)}"
                errors.append(error_msg)
                frappe.db.rollback()
                frappe.log_error(error_msg, "Bulk Depreciation Error")

        self.db_set('success_count', success_count)
        self.db_set('failed_count', failed_count)
        self.db_set('status', 'Completed')
        
        if errors:
            self.db_set('error_log', '\n'.join(errors[:50]))

        return {"success": success_count, "failed": failed_count}

    def get_or_create_branch(self):
        """Get or create a default branch for the company"""
        # Try to get any branch for the company (no is_default field)
        branch = frappe.db.get_value("Branch", {"company": self.company}, "name")
        
        if not branch:
            # Create a new branch
            try:
                branch_doc = frappe.new_doc("Branch")
                branch_doc.branch = f"{self.company} - Main"
                branch_doc.company = self.company
                branch_doc.save()
                frappe.db.commit()
                branch = branch_doc.name
                frappe.msgprint(_(f"✓ Created new branch '{branch}' for company {self.company}"))
            except Exception as e:
                frappe.log_error(f"Error creating branch: {str(e)}", "Bulk Depreciation")
                frappe.throw(_(f"Please create a branch for company {self.company} first"))
        
        return branch

    def on_submit(self):
        """Process all pending depreciation entries on submit"""
        if self.assets and len(self.assets) > 0:
            result = self.process_depreciation()
            frappe.msgprint(_(f"Processing complete. Success: {result.get('success', 0)}, Failed: {result.get('failed', 0)}"))