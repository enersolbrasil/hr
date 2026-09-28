# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    equipment_request_id = fields.Many2one(
        related="group_id.equipment_request_id", store=True
    )

    def _personal_equipment_auto_validate(self):
        """Validate the personal equipment transfers whose products are all
        reserved; the other ones are left to be validated by hand."""
        for picking in self:
            moves = picking.move_ids
            if any(m.state != "assigned" or m.has_tracking != "none" for m in moves):
                continue
            moves.picked = True
            try:
                with self.env.cr.savepoint():
                    picking.with_context(skip_sms=True).button_validate()
            except UserError:
                # e.g. an extra check prevents validating it automatically
                continue

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if picking.equipment_request_id:
                for move in picking.move_ids_without_package:
                    if move.state == "done":
                        request_lines = (
                            picking.equipment_request_id.sudo().line_ids.filtered(
                                lambda x, move=move: x.product_id == move.product_id
                            )
                        )
                        for line in request_lines:
                            if line.qty_delivered:
                                if line.quantity <= line.qty_delivered:
                                    line.validate_allocation()
        return res
