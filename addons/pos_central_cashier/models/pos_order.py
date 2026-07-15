# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    is_pending_payment = fields.Boolean(string="Pendiente de pago", default=False, index=True)
    precuenta_ref = fields.Char(string="Referencia precuenta", copy=False, index=True)
    source_order_id = fields.Many2one("pos.order", string="Orden origen (mostrador)", copy=False)

    @api.model
    def _next_precuenta_ref(self):
        return self.env["ir.sequence"].next_by_code("pos.central.cashier.precuenta") or "PENDIENTE"

    @api.model
    def mark_order_pending(self, order_id):
        order = self.browse(order_id).exists()
        if not order:
            raise UserError("No se encontró la orden para marcar pendiente.")
        if order.state in ("paid", "done", "invoiced"):
            raise UserError("La orden ya está pagada/finalizada.")
        if not order.precuenta_ref:
            order.precuenta_ref = self._next_precuenta_ref()
        order.is_pending_payment = True
        return {
            "order_id": order.id,
            "precuenta_ref": order.precuenta_ref,
            "name": order.name,
        }

    @api.model
    def search_pending_orders_for_pos(self, query="", limit=30):
        domain = [("is_pending_payment", "=", True), ("state", "in", ["draft", "paid"])]
        if query:
            domain.append("|")
            domain.append(("precuenta_ref", "ilike", query))
            domain.append(("partner_id.name", "ilike", query))
        orders = self.search(domain, order="id desc", limit=limit)
        return [
            {
                "id": o.id,
                "name": o.name,
                "precuenta_ref": o.precuenta_ref,
                "partner_name": o.partner_id.name or "",
                "amount_total": o.amount_total,
                "date_order": o.date_order,
            }
            for o in orders
        ]

    @api.model
    def export_pending_order_payload(self, order_id):
        order = self.browse(order_id).exists()
        if not order or not order.is_pending_payment:
            raise UserError("La orden seleccionada no está pendiente de pago.")
        return {
            "id": order.id,
            "name": order.name,
            "precuenta_ref": order.precuenta_ref,
            "partner_id": order.partner_id.id if order.partner_id else False,
            "lines": [
                {
                    "product_id": line.product_id.id,
                    "qty": line.qty,
                    "price_unit": line.price_unit,
                    "discount": line.discount,
                    "note": line.note,
                }
                for line in order.lines
            ],
        }

    def complete_pending_order_payment(self):
        """Mark pending orders as paid after successful payment at cashier."""
        for order in self:
            if order.is_pending_payment and order.source_order_id:
                # Mark the original counter order as paid too
                order.source_order_id.state = "paid"
                order.source_order_id.is_pending_payment = False
        return True
