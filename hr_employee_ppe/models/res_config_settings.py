# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ppe_block_expired_certification = fields.Boolean(
        related="company_id.ppe_block_expired_certification", readonly=False
    )
    ppe_require_signature = fields.Boolean(
        related="company_id.ppe_require_signature", readonly=False
    )
    ppe_expiry_notice_days = fields.Integer(
        related="company_id.ppe_expiry_notice_days", readonly=False
    )
    ppe_expiry_responsible_id = fields.Many2one(
        related="company_id.ppe_expiry_responsible_id", readonly=False
    )
