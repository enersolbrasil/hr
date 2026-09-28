# Copyright (C) 2015 Salton Massally (<smassally@idtlabs.sl>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # The age field uses a depends (birthday) that has defined
    # groups="hr.group_hr_user", if a user without permissions in HR tries to get
    # the value of this field will have an error.
    # The correct way to avoid this inconsistency is to define groups to field age
    age = fields.Integer(
        compute="_compute_age", search="_search_age", groups="hr.group_hr_user"
    )

    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            record.age = record._get_age()

    @api.model
    def _get_age_birthday_limit(self, age):
        """Return the latest birthday of the employees that are at least ``age``
        years old today."""
        today = fields.Date.context_today(self)
        limit = today - relativedelta(years=age)
        # relativedelta turns February 29th into February 28th on common years, so
        # the employees born on February 29th get one year older on February 28th
        if (
            (today.month, today.day) == (2, 28)
            and not calendar.isleap(today.year)
            and calendar.isleap(limit.year)
        ):
            limit += relativedelta(days=1)
        return limit

    def _search_age(self, operator, value):
        if operator in ("in", "not in"):
            sub_operator = "=" if operator == "in" else "!="
            domains = [self._search_age(sub_operator, age) for age in value]
            if operator == "in":
                return expression.OR(domains) if domains else expression.FALSE_DOMAIN
            return expression.AND(domains) if domains else expression.TRUE_DOMAIN
        if value is False and operator in ("=", "!="):
            return [("birthday", operator, False)]
        if operator not in ("=", "!=", "<", "<=", ">", ">="):
            raise UserError(self.env._("Operation not supported"))
        age = int(value)
        if operator == ">=":
            return [("birthday", "<=", self._get_age_birthday_limit(age))]
        if operator == ">":
            return [("birthday", "<=", self._get_age_birthday_limit(age + 1))]
        if operator == "<":
            return [("birthday", ">", self._get_age_birthday_limit(age))]
        if operator == "<=":
            return [("birthday", ">", self._get_age_birthday_limit(age + 1))]
        limit = self._get_age_birthday_limit(age)
        next_limit = self._get_age_birthday_limit(age + 1)
        if operator == "=":
            return [("birthday", "<=", limit), ("birthday", ">", next_limit)]
        return [
            "|",
            "|",
            ("birthday", "=", False),
            ("birthday", ">", limit),
            ("birthday", "<=", next_limit),
        ]
