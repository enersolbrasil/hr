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
    ppe_require_signature = fields.Boolean(
        string="Require PPE Signature",
        help="PPE can only be validated once the employee has signed their delivery.",
    )
    ppe_expiry_notice_days = fields.Integer(
        string="PPE Expiry Notice (Days)",
        default=30,
        help="Number of days before the expiry of a delivered PPE to schedule an "
        "activity to renew it. Set 0 to schedule no activity.",
    )
    ppe_expiry_responsible_id = fields.Many2one(
        comodel_name="res.users",
        string="PPE Renewal Responsible",
        help="User in charge of renewing the PPE that are about to expire. When "
        "empty, the activity is assigned to the user who accepted the request, "
        "or else to the manager of the employee.",
    )
