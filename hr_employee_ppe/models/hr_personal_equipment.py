# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrPersonalEquipment(models.Model):
    _inherit = "hr.personal.equipment"

    is_ppe = fields.Boolean(
        string="Is PPE",
        related="product_id.is_ppe",
        store=True,
        readonly=True,
    )
    indications = fields.Text(
        string="PPE Indications",
        related="product_id.indications",
        store=True,
        readonly=True,
        help="Situations in which the employee should use this equipment.",
    )
    expire_ppe = fields.Boolean(
        string="Expirable PPE",
        compute="_compute_expire_ppe",
        store=True,
        readonly=False,
        help="True if the PPE expires",
    )
    certification = fields.Char(
        string="Certification Number",
        related="product_id.ca_number",
        store=True,
        readonly=False,
        help="Certification Number (ex: CA no Brasil)",
    )
    issued_by = fields.Many2one(
        comodel_name="res.users",
        readonly=True,
    )
    employee_signature = fields.Binary(
        copy=False,
    )
    signed_on = fields.Datetime(
        copy=False,
        readonly=True,
    )

    @api.depends("product_id", "product_id.expirable_ppe")
    def _compute_expire_ppe(self):
        for rec in self:
            if rec.product_id:
                rec.expire_ppe = rec.product_id.expirable_ppe
            else:
                rec.expire_ppe = False

    def _accept_request_vals(self):
        res = super()._accept_request_vals()
        res["issued_by"] = self.env.user.id
        return res

    @api.onchange("product_id")
    def _compute_fields(self):
        for rec in self:
            if rec.product_id:
                rec.is_ppe = rec.product_id.is_ppe
                rec.expire_ppe = rec.product_id.expirable_ppe
                rec.indications = rec.product_id.indications
                if rec.product_id.ca_number:
                    rec.certification = rec.product_id.ca_number
            else:
                rec.is_ppe = False
                rec.expire_ppe = False
                rec.indications = False

    def _validate_allocation_vals(self):
        res = super()._validate_allocation_vals()
        start_date = self.start_date or fields.Date.context_today(self)
        if (
            not self.expiry_date
            and self.product_id.expirable_ppe
            and self.product_id.ppe_interval_type
        ):
            duration = self.product_id.ppe_duration or 0
            interval = self.product_id.ppe_interval_type
            interval_map = {
                "days": relativedelta(days=duration),
                "weeks": relativedelta(weeks=duration),
                "months": relativedelta(months=duration),
                "years": relativedelta(years=duration),
            }
            res["expiry_date"] = start_date + interval_map.get(
                interval, relativedelta(days=duration)
            )
        return res

    def validate_allocation(self):
        icp = self.env["ir.config_parameter"].sudo()
        block_ca = (
            icp.get_param("hr_employee_ppe.block_expired_ca", default="True") == "True"
        )
        require_sig = (
            icp.get_param("hr_employee_ppe.require_signature", default="False")
            == "True"
        )
        today = fields.Date.context_today(self)

        for rec in self:
            if (
                block_ca
                and rec.is_ppe
                and rec.product_id.ca_expiry_date
                and rec.product_id.ca_expiry_date < today
            ):
                msg = (
                    "The PPE '%(product)s' has an expired certification "
                    "(Certificate %(ca)s) as of %(date)s. Delivery is blocked."
                )
                raise ValidationError(
                    self.env._(
                        msg,
                        product=rec.product_id.display_name,
                        ca=rec.certification or rec.product_id.ca_number or "N/A",
                        date=rec.product_id.ca_expiry_date,
                    )
                )
            if require_sig and rec.is_ppe and not rec.employee_signature:
                msg = (
                    "Employee signature is required to validate PPE delivery for '%s'."
                )
                raise ValidationError(self.env._(msg, rec.product_id.display_name))
            if rec.employee_signature and not rec.signed_on:
                rec.signed_on = fields.Datetime.now()

        res = super().validate_allocation()
        self._check_dates()
        return res

    @api.model
    def cron_ppe_expiry_verification(self, date_ref=None):
        """Daily check for expired PPEs and schedule preventive renewal alerts."""
        if not date_ref:
            date_ref = fields.Date.context_today(self)

        # 1. Marcar EPIs vencidos
        expired_domain = [
            ("is_ppe", "=", True),
            ("expire_ppe", "=", True),
            ("state", "=", "valid"),
            ("expiry_date", "<", date_ref),
        ]
        expired_ppes = self.search(expired_domain)
        if expired_ppes:
            expired_ppes.write({"state": "expired"})
            for ppe in expired_ppes:
                ppe.message_post(
                    body=self.env._(
                        "PPE expired on %s. The equipment must be "
                        "replaced immediately.",
                        ppe.expiry_date,
                    )
                )

        # 2. Alerta preventivo com antecedência configurável (padrão 30 dias)
        icp = self.env["ir.config_parameter"].sudo()
        try:
            notice_days = int(
                icp.get_param("hr_employee_ppe.expiry_notice_days", default="30")
            )
        except (ValueError, TypeError):
            notice_days = 30

        if notice_days > 0:
            alert_limit = date_ref + relativedelta(days=notice_days)
            expiring_domain = [
                ("is_ppe", "=", True),
                ("expire_ppe", "=", True),
                ("state", "=", "valid"),
                ("expiry_date", ">=", date_ref),
                ("expiry_date", "<=", alert_limit),
            ]
            expiring_ppes = self.search(expiring_domain)
            if expiring_ppes:
                activity_type = self.env.ref(
                    "mail.mail_activity_data_todo", raise_if_not_found=False
                )
                if activity_type:
                    existing = self.env["mail.activity"].search(
                        [
                            ("res_id", "in", expiring_ppes.ids),
                            ("res_model", "=", "hr.personal.equipment"),
                            ("activity_type_id", "=", activity_type.id),
                        ]
                    )
                    notified_ids = set(existing.mapped("res_id"))
                    for ppe in expiring_ppes:
                        if ppe.id not in notified_ids:
                            target_user = (
                                ppe.issued_by
                                or ppe.employee_id.parent_id.user_id
                                or self.env.user
                            )
                            ppe.activity_schedule(
                                activity_type_id=activity_type.id,
                                summary=self.env._(
                                    "PPE Renewal: %s",
                                    ppe.product_id.display_name,
                                ),
                                note=self.env._(
                                    "The PPE '%(product)s' for employee %(employee)s "
                                    "expires on %(date)s. Please arrange for a "
                                    "preventive replacement.",
                                    product=ppe.product_id.display_name,
                                    employee=ppe.employee_id.name,
                                    date=ppe.expiry_date,
                                ),
                                user_id=target_user.id,
                                date_deadline=ppe.expiry_date,
                            )

    @api.constrains("start_date", "expiry_date", "expire_ppe")
    def _check_dates(self):
        for record in self:
            if record.expire_ppe and record.expiry_date:
                start_date = record.start_date or fields.Date.context_today(record)
                if record.expiry_date < start_date:
                    raise ValidationError(
                        self.env._("End date cannot occur earlier than start date.")
                    )
