# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MassHistoryTaxClearWizard(models.TransientModel):
    _name = 'data.correction.mass.history.tax.clear'
    _description = 'Wizard para Limpiar Impuestos Históricos Masivamente'

    module_to_clean = fields.Selection([
        ('purchase', 'Compras (Facturas de Proveedor y Órdenes)'),
        ('sale', 'Ventas (Módulo de Ventas)'),
        ('pos', 'Ventas (Punto de Venta)'),
    ], string='Módulo a Limpiar', required=True, default='pos')
    
    action_type = fields.Selection([
        ('clear', 'Borrar Impuestos (Dejar en 0%)'),
        ('replace', 'Reemplazar por Nuevo Impuesto')
    ], string='Acción a Realizar', default='clear', required=True)
    
    tax_id = fields.Many2one('account.tax', string='Nuevo Impuesto')

    date_from = fields.Date(string='Fecha Desde')
    date_to = fields.Date(string='Fecha Hasta')
    category_id = fields.Many2one('product.category', string='Categoría Específica', help='Opcional: Si seleccionas una categoría, solo se borrarán los impuestos de los productos de esta categoría (y sus subcategorías).')
    
    def action_clear_taxes(self):
        cleared_count = 0
        child_cats = False
        if self.category_id:
            child_cats = self.env['product.category'].search([('id', 'child_of', self.category_id.id)])
            
        if self.module_to_clean == 'pos':
            domain = []
            if self.date_from: domain.append(('date_order', '>=', self.date_from))
            if self.date_to: domain.append(('date_order', '<=', self.date_to))
            orders = self.env['pos.order'].search(domain)
            
            for order in orders:
                if hasattr(order, 'account_move') and order.account_move:
                    move = order.account_move
                    if move.state == 'posted': move.button_draft()
                    move.with_context(force_delete=True).unlink()
                
                # Evitamos usar order.write({'state': 'draft'}) porque el PdV bloquea la edición de órdenes cerradas.
                # Operaremos puramente con SQL para evitar el UserError("Esta orden ya está pagada...")
                
                for line in order.lines:
                    if child_cats and line.product_id.categ_id not in child_cats:
                        continue
                        
                    # Borrar impuestos previos (relación Many2Many)
                    self.env.cr.execute("DELETE FROM account_tax_pos_order_line_rel WHERE pos_order_line_id = %s", (line.id,))
                    
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    
                    if self.action_type == 'replace' and self.tax_id:
                        self.env.cr.execute("INSERT INTO account_tax_pos_order_line_rel (pos_order_line_id, account_tax_id) VALUES (%s, %s)", (line.id, self.tax_id.id))
                        currency = order.pricelist_id.currency_id if order.pricelist_id else order.company_id.currency_id
                        taxes = self.tax_id.compute_all(price, currency, line.qty, product=line.product_id, partner=order.partner_id)
                        price_subtotal = taxes['total_excluded']
                        price_subtotal_incl = taxes['total_included']
                    else:
                        price_subtotal = price * line.qty
                        price_subtotal_incl = price * line.qty
                    
                    self.env.cr.execute("""
                        UPDATE pos_order_line 
                        SET price_subtotal = %s, price_subtotal_incl = %s
                        WHERE id = %s
                    """, (price_subtotal, price_subtotal_incl, line.id))
                
                # Actualizar total de la orden
                self.env.cr.execute("SELECT SUM(price_subtotal), SUM(price_subtotal_incl) FROM pos_order_line WHERE order_id = %s", (order.id,))
                res = self.env.cr.fetchone()
                amount_untaxed = res[0] if res and res[0] else 0.0
                amount_total = res[1] if res and res[1] else 0.0
                amount_tax = amount_total - amount_untaxed
                
                self.env.cr.execute("""
                    UPDATE pos_order 
                    SET amount_tax = %s, amount_total = %s 
                    WHERE id = %s
                """, (amount_tax, amount_total, order.id))
                
                cleared_count += 1
                
        elif self.module_to_clean == 'sale':
            domain = []
            if self.date_from: domain.append(('date_order', '>=', self.date_from))
            if self.date_to: domain.append(('date_order', '<=', self.date_to))
            orders = self.env['sale.order'].search(domain)
            
            for order in orders:
                for inv in order.invoice_ids:
                    if inv.state == 'posted': inv.button_draft()
                    inv.button_cancel()
                    inv.with_context(force_delete=True).unlink()
                
                old_state = order.state
                if old_state not in ['draft', 'sent', 'cancel']: order.write({'state': 'draft'})
                
                for line in order.order_line:
                    if child_cats and line.product_id.categ_id not in child_cats:
                        continue
                        
                    if self.action_type == 'replace' and self.tax_id:
                        line.write({'tax_id': [(6, 0, [self.tax_id.id])]})
                    else:
                        line.write({'tax_id': [(5, 0, 0)]})
                
                if hasattr(order, '_amount_all'): order._amount_all()
                order.write({'state': old_state})
                cleared_count += 1
                
        elif self.module_to_clean == 'purchase':
            domain = []
            if self.date_from: domain.append(('date_approve', '>=', self.date_from))
            if self.date_to: domain.append(('date_approve', '<=', self.date_to))
            orders = self.env['purchase.order'].search(domain)
            
            for order in orders:
                for inv in order.invoice_ids:
                    if inv.state == 'posted': inv.button_draft()
                    if inv.state != 'cancel': inv.button_cancel()
                    inv.with_context(force_delete=True).unlink()
                
                old_state = order.state
                if old_state not in ['draft', 'sent', 'to approve', 'cancel']: order.write({'state': 'draft'})
                
                for line in order.order_line:
                    if child_cats and line.product_id.categ_id not in child_cats:
                        continue
                        
                    if self.action_type == 'replace' and self.tax_id:
                        line.write({'taxes_id': [(6, 0, [self.tax_id.id])]})
                    else:
                        line.write({'taxes_id': [(5, 0, 0)]})
                
                if hasattr(order, '_amount_all'): order._amount_all()
                order.write({'state': old_state})
                cleared_count += 1
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Limpieza Histórica Completada"),
                'message': _("Se han eliminado los impuestos y asientos de %s registros históricos.", cleared_count),
                'type': 'success',
                'sticky': False,
            }
        }
