# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ppe_block_expired_certification = fields.Boolean(
        string="Block PPE with Expired Certification",
        default=True,
        help="Prevent accepting requests and validating allocations of PPE whose "
        "certification has expired.",
    )
