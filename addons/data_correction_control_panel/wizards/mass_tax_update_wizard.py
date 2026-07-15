# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MassTaxUpdateWizard(models.TransientModel):
    _name = 'data.correction.mass.tax.update'
    _description = 'Actualización Masiva de Impuestos en Maestro'

    category_id = fields.Many2one('product.category', string='Categoría de Ítems', required=True)
    update_type = fields.Selection([
        ('add_sale', 'Atribuir Impuesto de Venta'),
        ('remove_sale', 'Quitar Impuesto de Venta'),
        ('add_purchase', 'Atribuir Impuesto de Compra'),
        ('remove_purchase', 'Quitar Impuesto de Compra'),
        ('clear_all_sale', 'Quitar TODO impuesto de Venta'),
        ('clear_all_purchase', 'Quitar TODO impuesto de Compra'),
    ], string='Tipo de Actualización', required=True, default='add_sale')
    
    tax_id = fields.Many2one('account.tax', string='Impuesto', domain=[('type_tax_use', '=', 'sale')])

    @api.onchange('update_type')
    def _onchange_update_type(self):
        if self.update_type in ('add_sale', 'remove_sale'):
            return {'domain': {'tax_id': [('type_tax_use', '=', 'sale')]}}
        elif self.update_type in ('add_purchase', 'remove_purchase'):
            return {'domain': {'tax_id': [('type_tax_use', '=', 'purchase')]}}
        else:
            self.tax_id = False

    def action_apply_mass_update(self):
        # Buscar productos en la categoría o subcategorías
        products = self.env['product.template'].search([('categ_id', 'child_of', self.category_id.id)])
        
        if not products:
            return

        for product in products:
            if self.update_type == 'add_sale' and self.tax_id:
                product.taxes_id = [(4, self.tax_id.id)]
            elif self.update_type == 'remove_sale' and self.tax_id:
                product.taxes_id = [(3, self.tax_id.id)]
            elif self.update_type == 'clear_all_sale':
                product.taxes_id = [(5, 0, 0)]
            elif self.update_type == 'add_purchase' and self.tax_id:
                product.supplier_taxes_id = [(4, self.tax_id.id)]
            elif self.update_type == 'remove_purchase' and self.tax_id:
                product.supplier_taxes_id = [(3, self.tax_id.id)]
            elif self.update_type == 'clear_all_purchase':
                product.supplier_taxes_id = [(5, 0, 0)]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Éxito"),
                'message': _("Se actualizaron los impuestos de %s ítems.", len(products)),
                'type': 'success',
                'sticky': False,
            }
        }
