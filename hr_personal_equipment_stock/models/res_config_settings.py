# Copyright 2024 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ppe_source_location_id = fields.Many2one(
        related="company_id.ppe_source_location_id",
        readonly=False,
    )
    ppe_dest_location_id = fields.Many2one(
        related="company_id.ppe_dest_location_id",
        readonly=False,
    )
    ppe_picking_type_id = fields.Many2one(
        related="company_id.ppe_picking_type_id",
        readonly=False,
    )
    ppe_auto_validate_stock = fields.Boolean(
        related="company_id.ppe_auto_validate_stock",
        readonly=False,
    )
