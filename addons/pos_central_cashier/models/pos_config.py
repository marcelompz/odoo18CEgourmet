# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_counter_pos = fields.Boolean(
        string="PDV Mostrador",
        help="Si está activo, este PDV puede marcar órdenes como pendiente de pago.",
    )
    is_central_cashier = fields.Boolean(
        string="PDV Caja Principal",
        help="Si está activo, este PDV puede recuperar y cobrar órdenes pendientes.",
    )

    @api.constrains("is_counter_pos", "is_central_cashier")
    def _check_mutual_exclusion(self):
        for record in self:
            if record.is_counter_pos and record.is_central_cashier:
                raise ValidationError(
                    _("A POS cannot be both 'Counter POS' and 'Central Cashier' at the same time. "
                      "Please choose only one role.")
                )