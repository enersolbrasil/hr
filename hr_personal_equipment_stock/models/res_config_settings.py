# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    personal_equipment_picking_type_id = fields.Many2one(
        related="company_id.personal_equipment_picking_type_id", readonly=False
    )
    personal_equipment_auto_validate = fields.Boolean(
        related="company_id.personal_equipment_auto_validate", readonly=False
    )
