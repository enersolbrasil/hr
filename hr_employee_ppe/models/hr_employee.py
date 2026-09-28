# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    ppe_ids = fields.One2many(
        comodel_name="hr.personal.equipment",
        inverse_name="employee_id",
        string="PPE",
        domain=[("is_ppe", "=", True), ("state", "not in", ["draft", "cancelled"])],
        groups="hr.group_hr_user",
    )
