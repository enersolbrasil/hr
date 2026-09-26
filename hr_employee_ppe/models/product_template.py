# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_ppe = fields.Boolean(string="Is PPE", default=False)
    indications = fields.Text(
        string="PPE Indications",
        help="Situations in which the employee should use this equipment. Only for ppe",
    )
    expirable_ppe = fields.Boolean(
        string="Expirable PPE",
        help="Select this option if the PPE has expiry date.",
        default=False,
    )
    ppe_duration = fields.Integer(string="PPE duration")
    ppe_interval_type = fields.Selection(
        [
            ("days", "Days"),
            ("weeks", "Weeks"),
            ("months", "Months"),
            ("years", "Years"),
        ],
        string="Interval Unit",
    )
    ca_number = fields.Char(
        string="Certification / CA Number",
        help="Certificado de Aprovação (CA) emitido pelo Ministério do Trabalho",
    )
    ca_expiry_date = fields.Date(
        string="CA Expiry Date",
        help="Data de validade do CA perante o Ministério do Trabalho",
    )
