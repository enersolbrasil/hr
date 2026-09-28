# Copyright 2020 Escodoo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date


class HrPersonalEquipment(models.Model):
    _name = "hr.personal.equipment"
    _inherit = ["hr.personal.equipment"]

    is_ppe = fields.Boolean(related="product_id.is_ppe", store=True)
    indications = fields.Text(
        related="product_id.indications",
        store=True,
        help="Situations in which the employee should use this equipment.",
    )
    expire_ppe = fields.Boolean(
        compute="_compute_expire_ppe",
        store=True,
        readonly=False,
        help="True if the PPE expires",
    )
    certification = fields.Char(
        string="Certification Number",
        # copied from the product, so that the allocation keeps the certification
        # of the delivered PPE when the one of the product is renewed
        compute="_compute_certification",
        store=True,
        readonly=False,
        help="Certification Number",
    )
    issued_by = fields.Many2one(comodel_name="res.users")
    expiry_notice_sent = fields.Boolean(
        copy=False,
        readonly=True,
        help="An activity has been scheduled to renew this PPE before its expiry.",
    )

    def _accept_request_vals(self):
        res = super()._accept_request_vals()
        res["issued_by"] = self.env.user.id
        return res

    @api.depends("product_id")
    def _compute_expire_ppe(self):
        for rec in self:
            rec.expire_ppe = rec.product_id.expirable_ppe

    @api.depends("product_id")
    def _compute_certification(self):
        for rec in self:
            rec.certification = rec.product_id.ppe_certification

    def _check_ppe_certification(self):
        """Prevent delivering PPE whose certification has expired."""
        today = fields.Date.context_today(self)
        for rec in self:
            expiry_date = rec.product_id.ppe_certification_expiry_date
            company = rec.employee_id.company_id or self.env.company
            if (
                rec.is_ppe
                and expiry_date
                and expiry_date < today
                and company.ppe_block_expired_certification
            ):
                raise UserError(
                    self.env._(
                        "The certification of %(product)s expired on %(date)s, so "
                        "it cannot be delivered.",
                        product=rec.product_id.display_name,
                        date=format_date(self.env, expiry_date),
                    )
                )

    def _accept_request(self):
        self._check_ppe_certification()
        return super()._accept_request()

    def _validate_allocation_vals(self):
        res = super()._validate_allocation_vals()
        start_date = res.get("start_date") or self.start_date
        product = self.product_id
        if not self.expiry_date and product.expirable_ppe and product.ppe_interval_type:
            # the interval types are named after the relativedelta arguments
            res["expiry_date"] = start_date + relativedelta(
                **{product.ppe_interval_type: product.ppe_duration}
            )
        return res

    def validate_allocation(self):
        self._check_ppe_certification()
        res = super().validate_allocation()
        self._check_dates()
        return res

    @api.model
    def cron_ppe_expiry_verification(self, date_ref=None):
        if not date_ref:
            date_ref = fields.Date.context_today(self)
        date_ref = fields.Date.to_date(date_ref)
        # only the delivered equipment can expire
        self.search([("state", "=", "valid"), ("expiry_date", "<", date_ref)]).write(
            {"state": "expired"}
        )
        self._schedule_ppe_renewal_activities(date_ref)

    @api.model
    def _schedule_ppe_renewal_activities(self, date_ref):
        """Schedule an activity to renew the delivered PPE that expire soon."""
        companies = self.env["res.company"].search([("ppe_expiry_notice_days", ">", 0)])
        for company in companies:
            limit_date = date_ref + relativedelta(days=company.ppe_expiry_notice_days)
            allocations = self.search(
                [
                    ("is_ppe", "=", True),
                    ("state", "=", "valid"),
                    ("expiry_notice_sent", "=", False),
                    ("employee_id.company_id", "=", company.id),
                    ("expiry_date", ">=", date_ref),
                    ("expiry_date", "<=", limit_date),
                ]
            )
            for allocation in allocations:
                user = allocation._get_ppe_renewal_user()
                if user:
                    allocation.activity_schedule(
                        "hr_employee_ppe.mail_activity_type_ppe_renewal",
                        date_deadline=allocation.expiry_date,
                        user_id=user.id,
                    )
            allocations.expiry_notice_sent = True

    def _get_ppe_renewal_user(self):
        self.ensure_one()
        return (
            self.employee_id.company_id.ppe_expiry_responsible_id
            or self.issued_by
            or self.employee_id.parent_id.user_id
        )

    def write(self, vals):
        if "expiry_date" in vals and "expiry_notice_sent" not in vals:
            # a new expiry date deserves a new notice
            vals = dict(vals, expiry_notice_sent=False)
        return super().write(vals)

    def _check_dates(self):
        for record in self:
            if record.expire_ppe and record.expiry_date:
                start_date = record.start_date or fields.Date.context_today(record)
                if record.expiry_date < start_date:
                    raise ValidationError(
                        self.env._("End date cannot occur earlier than start date.")
                    )
