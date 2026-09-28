# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrPersonalEquipmentSignatureMixin(models.AbstractModel):
    _name = "hr.personal.equipment.signature.mixin"
    _description = "Employee signature of personal equipment"

    employee_signature = fields.Binary(copy=False)
    signed_on = fields.Datetime(copy=False, readonly=True)

    @api.model
    def _prepare_signature_vals(self, vals):
        """Record when the employee signature is drawn or removed."""
        if "employee_signature" in vals and "signed_on" not in vals:
            signed_on = fields.Datetime.now() if vals["employee_signature"] else False
            vals = dict(vals, signed_on=signed_on)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._prepare_signature_vals(v) for v in vals_list])

    def write(self, vals):
        return super().write(self._prepare_signature_vals(vals))
