# Copyright 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    first_contract_id = fields.Many2one(
        "hr.contract",
        compute="_compute_first_contract_id",
        store=True,
        prefetch=False,
        help="First contract of the employee",
    )
    last_contract_id = fields.Many2one(
        "hr.contract",
        compute="_compute_last_contract_id",
        store=True,
        prefetch=False,
        help="Last contract of the employee",
    )
    service_start_date = fields.Date(
        string="Start Date",
        readonly=True,
        related="first_contract_id.date_start",
        prefetch=False,
    )
    service_termination_date = fields.Date(
        string="Termination Date",
        readonly=True,
        related="last_contract_id.date_end",
        prefetch=False,
    )

    @api.depends("contract_ids", "contract_ids.state", "contract_ids.date_start")
    def _compute_first_contract_id(self):
        states = self._get_service_contract_states()
        for employee in self:
            valid_contracts = employee.contract_ids.filtered(
                lambda c: c.state in states and c.date_start
            )
            employee.first_contract_id = (
                valid_contracts.sorted("date_start")[:1] if valid_contracts else False
            )

    @api.depends(
        "contract_ids",
        "contract_ids.state",
        "contract_ids.date_end",
        "contract_ids.date_start",
    )
    def _compute_last_contract_id(self):
        states = self._get_service_contract_states()
        far_future = fields.Date.to_date("9999-12-31")
        for employee in self:
            valid_contracts = employee.contract_ids.filtered(
                lambda c: c.state in states and c.date_start
            )
            employee.last_contract_id = (
                valid_contracts.sorted(
                    lambda c: (
                        c.date_end or far_future,
                        c.date_start or fields.Date.to_date("1900-01-01"),
                    ),
                    reverse=True,
                )[:1]
                if valid_contracts
                else False
            )

    @api.onchange("service_hire_date")
    def _onchange_service_hire_date(self):  # pragma: no cover
        # Do nothing
        pass

    def _get_contract_filter(self):
        self.ensure_one()

        return [
            ("employee_id", "=", self.id),
            ("state", "in", self._get_service_contract_states()),
        ]

    @api.model
    def _get_service_contract_states(self):
        return ["open", "pending", "close"]
