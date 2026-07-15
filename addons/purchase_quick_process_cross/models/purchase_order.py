# -*- coding: utf-8 -*-
"""
Created on 2025-11-23 17:30:58

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    def action_reception_and_create_invoice(self):
        """
        Esta función realiza el flujo completo:
        1. Confirma el pedido de compra si está en borrador o enviado.
        2. Valida la recepción de los productos.
        3. Crea la factura de proveedor en estado borrador.
        4. Devuelve una acción para abrir la factura recién creada.
        """
        self.ensure_one()

        if self.state in ['draft', 'sent']:
            self.button_confirm()
        
        self.flush_model(['state'])

        if self.state not in ['purchase', 'done']:
             raise UserError(f"El pedido de compra debe estar en estado 'Pedido de Compra' para continuar. Estado actual: {self.state}")

        if self.picking_ids:
            pickings_to_validate = self.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))

            for picking in pickings_to_validate:
                res = picking.button_validate()

                if res and isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
                    wizard = self.env[res['res_model']].with_context(res['context']).create({'backorder': False})
                    wizard.process()

        action = self.action_create_invoice()
        
        new_invoice = self.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        if not new_invoice:
            raise UserError("No se pudo crear o encontrar una nueva factura en borrador.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Factura de Proveedor',
            'res_model': 'account.move',
            'res_id': new_invoice[-1].id,
            'view_mode': 'form',
            'target': 'current',
        }
