# Copyright (C) 2015 Salton Massally (<smassally@idtlabs.sl>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # The age field uses a depends (birthday) that has defined
    # groups="hr.group_hr_user", if a user without permissions in HR tries to get
    # the value of this field will have an error.
    # The correct way to avoid this inconsistency is to define groups to field age
    age = fields.Integer(
        compute="_compute_age",
        search="_search_age",
        groups="hr.group_hr_user",
    )

    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            record.age = record._get_age() if record.birthday else False

    def _search_age(self, operator, value):
        if value is False or value is None:
            return [("birthday", "=", False)]
        try:
            val = int(value)
        except (ValueError, TypeError):
            return []

        today = fields.Date.context_today(self)
        res = []
        if operator in (">=", "<"):
            target_date = today - relativedelta(years=val)
            inv_op = "<=" if operator == ">=" else ">"
            res = [("birthday", inv_op, target_date)]
        elif operator in (">", "<="):
            target_date = today - relativedelta(years=val + 1)
            inv_op = "<=" if operator == ">" else ">"
            res = [("birthday", inv_op, target_date)]
        elif operator == "=":
            max_date = today - relativedelta(years=val)
            min_date = today - relativedelta(years=val + 1)
            res = [("birthday", "<=", max_date), ("birthday", ">", min_date)]
        elif operator == "!=":
            max_date = today - relativedelta(years=val)
            min_date = today - relativedelta(years=val + 1)
            res = ["|", ("birthday", ">", max_date), ("birthday", "<=", min_date)]
        return res
