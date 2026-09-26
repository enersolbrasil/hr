# Copyright 2024 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ppe_source_location_id = fields.Many2one(
        "stock.location",
        string="Default PPE Source Location",
        help="Default source location from which PPE and equipment are issued.",
    )
    ppe_dest_location_id = fields.Many2one(
        "stock.location",
        string="Default PPE Destination Location",
        help=(
            "Destination location where PPE is issued as operational "
            "consumption or workplace safety expense."
        ),
    )
    ppe_picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="PPE Operation Type",
        help="Operation type used for PPE inventory dispatches.",
    )
    ppe_auto_validate_stock = fields.Boolean(
        string="Auto Validate PPE Stock Delivery",
        default=True,
        help=(
            "If active, accepting the equipment request validates the stock "
            "delivery immediately without requiring manual picking validation."
        ),
    )

    def _get_or_create_ppe_picking_type(self):
        """Return configured PPE operation type or auto-create one."""
        self.ensure_one()
        if self.ppe_picking_type_id:
            return self.ppe_picking_type_id

        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.id)], limit=1
        )
        if not warehouse:
            return False

        # Check if an existing dedicated PPE operation type exists
        existing = self.env["stock.picking.type"].search(
            [
                ("company_id", "=", self.id),
                ("warehouse_id", "=", warehouse.id),
                ("sequence_code", "=", "PPE"),
            ],
            limit=1,
        )
        if existing:
            self.sudo().ppe_picking_type_id = existing
            return existing

        source_loc = (
            self.ppe_source_location_id
            or warehouse.lot_stock_id
            or self.env.ref("stock.stock_location_stock", raise_if_not_found=False)
        )
        dest_loc = self.ppe_dest_location_id or self.env.ref(
            "stock.stock_location_customers", raise_if_not_found=False
        )

        try:
            sequence = (
                self.env["ir.sequence"]
                .sudo()
                .create(
                    {
                        "name": f"{warehouse.name} PPE Delivery Sequence",
                        "prefix": f"{warehouse.code}/PPE/",
                        "padding": 5,
                        "company_id": self.id,
                    }
                )
            )
            picking_type = (
                self.env["stock.picking.type"]
                .sudo()
                .create(
                    {
                        "name": "PPE Delivery",
                        "sequence_code": "PPE",
                        "code": "internal",
                        "sequence_id": sequence.id,
                        "warehouse_id": warehouse.id,
                        "default_location_src_id": (
                            source_loc.id if source_loc else False
                        ),
                        "default_location_dest_id": dest_loc.id if dest_loc else False,
                        "company_id": self.id,
                    }
                )
            )
            self.sudo().ppe_picking_type_id = picking_type
            return picking_type
        except Exception:  # noqa: BLE001 # pylint: disable=broad-exception-caught
            return warehouse.int_type_id
