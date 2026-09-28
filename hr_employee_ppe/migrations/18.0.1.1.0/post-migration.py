# Copyright 2026 Enersol Brasil
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Align the PPE data of the existing allocations with their product.

    These fields used to be copied from the product by an onchange only, so
    allocations created without the form may not reflect their product.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    allocations = env["hr.personal.equipment"].search([])
    for fname in ("is_ppe", "indications"):
        env.add_to_compute(allocations._fields[fname], allocations)
    allocations.flush_recordset()
