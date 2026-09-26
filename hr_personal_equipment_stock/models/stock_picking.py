# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    equipment_request_id = fields.Many2one(
        related="group_id.equipment_request_id", store=True
    )

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            if not picking.equipment_request_id:
                continue
            done_moves = picking.move_ids_without_package.filtered(
                lambda m: m.state == "done"
            )
            for move in done_moves:
                request_lines = picking.equipment_request_id.sudo().line_ids.filtered(
                    lambda x, m=move: x.product_id == m.product_id
                )
                for line in request_lines:
                    if line.qty_delivered and line.quantity <= line.qty_delivered:
                        line.validate_allocation()
        return res
