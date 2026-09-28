# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template"]

    is_ppe = fields.Boolean(default=False)
    indications = fields.Text(
        help="Situations in which the employee should use this equipment. Only for ppe",
    )
    expirable_ppe = fields.Boolean(
        help="Select this option if the PPE has expiry date.", default=False
    )
    ppe_duration = fields.Integer(string="PPE duration")
    ppe_interval_type = fields.Selection(
        [
            ("minutes", "Minutes"),
            ("hours", "Hours"),
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
            ("years", "Years"),
        ],
        string="Interval Unit",
    )
    ppe_certification = fields.Char(
        string="Certification Number",
        help="Number of the certificate of this PPE, copied to the PPE delivered "
        "to the employees.",
    )
    ppe_certification_expiry_date = fields.Date(
        string="Certification Expiry Date",
        help="Last day of validity of the certificate of this PPE. Once it has "
        "expired, the PPE cannot be delivered unless the Employees settings allow "
        "it.",
    )
