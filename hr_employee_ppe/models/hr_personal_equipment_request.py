# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrPersonalEquipmentRequest(models.Model):
    _inherit = "hr.personal.equipment.request"

    contains_ppe = fields.Boolean(
        string="Contains PPE",
        compute="_compute_contains_ppe",
        store=True,
    )
    employee_signature = fields.Binary(
        copy=False,
    )
    signed_on = fields.Datetime(
        copy=False,
        readonly=True,
    )

    @api.depends("line_ids.is_ppe")
    def _compute_contains_ppe(self):
        for rec in self:
            rec.contains_ppe = any(line.is_ppe for line in rec.line_ids)

    def accept_request(self):
        icp = self.env["ir.config_parameter"].sudo()
        require_sig = (
            icp.get_param("hr_employee_ppe.require_signature", default="False")
            == "True"
        )
        for rec in self:
            if require_sig and rec.contains_ppe:
                has_request_sig = bool(rec.employee_signature)
                has_all_line_sigs = all(
                    bool(line.employee_signature)
                    for line in rec.line_ids
                    if line.is_ppe
                )
                if not (has_request_sig or has_all_line_sigs):
                    raise ValidationError(
                        self.env._(
                            "Employee signature is required to accept "
                            "and deliver PPE for request '%s'.",
                            rec.display_name,
                        )
                    )
            if rec.employee_signature:
                if not rec.signed_on:
                    rec.signed_on = fields.Datetime.now()
                unsigned_lines = rec.line_ids.filtered(
                    lambda l: l.is_ppe and not l.employee_signature
                )
                if unsigned_lines:
                    unsigned_lines.write(
                        {
                            "employee_signature": rec.employee_signature,
                            "signed_on": rec.signed_on,
                        }
                    )
        return super().accept_request()

    def action_view_ppe_report(self):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "hr_employee_ppe.hr_employee_ppe_report_template"
        )
        return report.report_action(self)
