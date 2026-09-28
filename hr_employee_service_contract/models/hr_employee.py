# Copyright 2018 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    first_contract_id = fields.Many2one(
        "hr.contract",
        compute="_compute_first_contract_id",
        store=True,
        prefetch=False,
        string="First Contract",
        help="First contract of the employee",
    )
    last_contract_id = fields.Many2one(
        "hr.contract",
        compute="_compute_last_contract_id",
        store=True,
        prefetch=False,
        string="Last Contract",
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

    def _get_service_contracts(self):
        """Return the contracts of the employee that count for its service."""
        self.ensure_one()
        return self.contract_ids.filtered_domain(self._get_contract_filter()).filtered(
            "date_start"
        )

    @api.depends("contract_ids", "contract_ids.state", "contract_ids.date_start")
    def _compute_first_contract_id(self):
        # The contracts are read through the prefetched one2many instead of one
        # search per employee
        for employee in self:
            employee.first_contract_id = employee._get_service_contracts().sorted(
                "date_start"
            )[:1]

    @api.depends(
        "contract_ids",
        "contract_ids.state",
        "contract_ids.date_start",
        "contract_ids.date_end",
    )
    def _compute_last_contract_id(self):
        for employee in self:
            # Open-ended contracts come first, then the latest end and start dates
            employee.last_contract_id = employee._get_service_contracts().sorted(
                lambda contract: (
                    contract.date_end or date.max,
                    contract.date_start,
                ),
                reverse=True,
            )[:1]

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
