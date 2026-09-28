# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    personal_equipment_picking_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="Personal Equipment Operation Type",
        help="When set, the accepted equipment requests are delivered with a "
        "transfer of this operation type, from its default source location to the "
        "location of the request, instead of running the procurement rules.",
    )
    personal_equipment_auto_validate = fields.Boolean(
        string="Validate Personal Equipment Transfers",
        help="Validate the transfers of the equipment requests as soon as all "
        "their products are reserved.",
    )
