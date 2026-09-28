# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrPersonalEquipmentRequest(models.Model):
    _name = "hr.personal.equipment.request"
    _inherit = [
        "hr.personal.equipment.request",
        "hr.personal.equipment.signature.mixin",
    ]

    contains_ppe = fields.Boolean(compute="_compute_contains_ppe")

    @api.depends("line_ids.is_ppe")
    def _compute_contains_ppe(self):
        for rec in self:
            contains_ppe = False
            for line in rec.line_ids:
                if line.is_ppe:
                    contains_ppe = True
                    break
            rec.contains_ppe = contains_ppe

    def action_view_ppe_report(self):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "hr_employee_ppe.hr_employee_ppe_report_template"
        )
        return report.report_action(self)
