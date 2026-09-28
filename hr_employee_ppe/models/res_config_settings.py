# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ppe_block_expired_certification = fields.Boolean(
        related="company_id.ppe_block_expired_certification", readonly=False
    )
