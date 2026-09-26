# Copyright 2024 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ppe_expiry_notice_days = fields.Integer(
        string="Aviso Prévio de Vencimento (Dias)",
        config_parameter="hr_employee_ppe.expiry_notice_days",
        default=30,
        help=(
            "Dias de antecedência para alertar o SESMT e o colaborador "
            "sobre o vencimento de EPIs."
        ),
    )
    ppe_block_expired_ca = fields.Boolean(
        string="Bloquear Entrega com CA Vencido",
        config_parameter="hr_employee_ppe.block_expired_ca",
        default=True,
        help=(
            "Impede a validação de alocações caso o Certificado de Aprovação "
            "perante o MTE esteja expirado."
        ),
    )
    ppe_require_signature = fields.Boolean(
        string="Exigir Assinatura na Entrega",
        config_parameter="hr_employee_ppe.require_signature",
        default=False,
        help=(
            "Se marcado, a alocação só é validada após o registro de "
            "assinatura na tela ou comprovante anexado."
        ),
    )
    ppe_signature_method = fields.Selection(
        [
            ("touch", "Assinatura na Tela (Tablet / Touch)"),
            ("upload", "Upload de Termo Digitalizado (PDF/Foto)"),
            ("both", "Permitir Tela ou Upload"),
        ],
        string="Modo de Assinatura Permitido",
        config_parameter="hr_employee_ppe.signature_method",
        default="both",
    )
