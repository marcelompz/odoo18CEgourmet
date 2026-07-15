# -*- coding: utf-8 -*-
from odoo import models, _

class DataCorrectionDashboard(models.TransientModel):
    _name = 'data.correction.dashboard'
    _description = 'Panel de control de correcciones'

    def action_detect_purchase(self):
        """
        Detecta inconsistencias comparando los impuestos aplicados en las facturas 
        de proveedor (account.move.line) vs los impuestos de compra del maestro de ítems.
        """
        # 1. Limpiar inconsistencias previas no resueltas de compras para no duplicar
        self.env['data.correction.inconsistency'].search([
            ('source_model', '=', 'purchase'),
            ('field_to_correct', '=', 'tax_ids'),
            ('state', '=', 'draft')
        ]).unlink()

        # 2. Buscar líneas de facturas de proveedor (compras)
        invoice_lines = self.env['account.move.line'].search([
            ('move_id.move_type', 'in', ['in_invoice', 'in_receipt']),
            ('display_type', '=', 'product'),
            ('product_id', '!=', False)
        ])

        inconsistencies = []
        for line in invoice_lines:
            applied_taxes = line.tax_ids
            master_taxes = line.product_id.supplier_taxes_id

            # Si los IDs de los impuestos no coinciden exactamente, hay una inconsistencia
            if set(applied_taxes.ids) != set(master_taxes.ids):
                old_val = ", ".join(applied_taxes.mapped('name')) or "Sin impuestos"
                new_val = ", ".join(master_taxes.mapped('name')) or "Sin impuestos"
                
                inconsistencies.append({
                    'item_id': line.product_id.id,
                    'source_model': 'purchase',
                    'source_record_id': line.id,
                    'source_record_name': line.move_id.name,
                    'field_to_correct': 'tax_ids',
                    'old_value': old_val,
                    'new_value': new_val,
                    'state': 'draft',
                })
        
        # 3. Crear registros masivos si se encontraron errores
        if inconsistencies:
            self.env['data.correction.inconsistency'].create(inconsistencies)
        
        # Recargar el panel para actualizar los contadores
        return self._reload_dashboard()

    def action_detect_pos(self):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("--- START action_detect_pos ---")
        
        self.env['data.correction.inconsistency'].search([
            ('source_model', '=', 'pos'),
            ('field_to_correct', '=', 'tax_ids'),
            ('state', '=', 'draft')
        ]).unlink()

        pos_lines = self.env['pos.order.line'].search([
            ('product_id', '!=', False)
        ])
        
        _logger.info(f"Found {len(pos_lines)} pos_order_line records to evaluate.")

        inconsistencies = []
        for line in pos_lines:
            applied_taxes = line.tax_ids_after_fiscal_position if hasattr(line, 'tax_ids_after_fiscal_position') else line.tax_ids
            master_taxes = line.product_id.taxes_id

            if set(applied_taxes.ids) != set(master_taxes.ids):
                old_val = ", ".join(applied_taxes.mapped('name')) or "Sin impuestos"
                new_val = ", ".join(master_taxes.mapped('name')) or "Sin impuestos"
                
                inconsistencies.append({
                    'item_id': line.product_id.id,
                    'source_model': 'pos',
                    'source_record_id': line.id,
                    'source_record_name': line.order_id.name,
                    'field_to_correct': 'tax_ids',
                    'old_value': old_val,
                    'new_value': new_val,
                    'state': 'draft',
                })
        
        _logger.info(f"Found {len(inconsistencies)} inconsistencies in POS.")
        if inconsistencies:
            self.env['data.correction.inconsistency'].create(inconsistencies)
            _logger.info("Inconsistencies created successfully in the DB.")
        
        return self._reload_dashboard()

    def action_detect_sale(self):
        self.env['data.correction.inconsistency'].search([
            ('source_model', '=', 'sale'),
            ('field_to_correct', '=', 'tax_id'),
            ('state', '=', 'draft')
        ]).unlink()

        sale_lines = self.env['sale.order.line'].search([
            ('display_type', '=', False),
            ('product_id', '!=', False)
        ])

        inconsistencies = []
        for line in sale_lines:
            # sale.order.line utiliza 'tax_id' para su campo Many2many de impuestos
            applied_taxes = line.tax_id
            master_taxes = line.product_id.taxes_id

            if set(applied_taxes.ids) != set(master_taxes.ids):
                old_val = ", ".join(applied_taxes.mapped('name')) or "Sin impuestos"
                new_val = ", ".join(master_taxes.mapped('name')) or "Sin impuestos"
                
                inconsistencies.append({
                    'item_id': line.product_id.id,
                    'source_model': 'sale',
                    'source_record_id': line.id,
                    'source_record_name': line.order_id.name,
                    'field_to_correct': 'tax_id',
                    'old_value': old_val,
                    'new_value': new_val,
                    'state': 'draft',
                })
        
        if inconsistencies:
            self.env['data.correction.inconsistency'].create(inconsistencies)
        
        return self._reload_dashboard()

    def action_detect_zero_cost(self):
        """ Detectar líneas de venta (POS o Sale) de productos con costo cero que fueron vendidos. """
        self.env['data.correction.inconsistency'].search([
            ('field_to_correct', '=', 'Costo'),
            ('state', '=', 'draft')
        ]).unlink()

        inconsistencies = []

        # 1. Ventas PdV
        pos_lines = self.env['pos.order.line'].search([('product_id', '!=', False)])
        for line in pos_lines:
            price_unit_discounted = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if price_unit_discounted > 0.0 and (line.product_id.standard_price <= 0.0 or price_unit_discounted <= line.product_id.standard_price):
                inconsistencies.append({
                    'item_id': line.product_id.id,
                    'source_model': 'pos',
                    'source_record_id': line.id,
                    'source_record_name': f"{line.order_id.name} (Línea {line.id})",
                    'field_to_correct': 'Costo',
                    'old_value': str(line.product_id.standard_price),
                    'new_value': 'Revisar Costo/PV',
                    'precio_venta': price_unit_discounted,
                    'state': 'draft',
                })

        # 2. Ventas Módulo Default
        sale_lines = self.env['sale.order.line'].search([('display_type', '=', False), ('product_id', '!=', False)])
        for line in sale_lines:
            price_unit_discounted = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            if price_unit_discounted > 0.0 and (line.product_id.standard_price <= 0.0 or price_unit_discounted <= line.product_id.standard_price):
                inconsistencies.append({
                    'item_id': line.product_id.id,
                    'source_model': 'sale',
                    'source_record_id': line.id,
                    'source_record_name': f"{line.order_id.name} (Línea {line.id})",
                    'field_to_correct': 'Costo',
                    'old_value': str(line.product_id.standard_price),
                    'new_value': 'Revisar Costo/PV',
                    'precio_venta': price_unit_discounted,
                    'state': 'draft',
                })

        if inconsistencies:
            self.env['data.correction.inconsistency'].create(inconsistencies)
        
        return self._reload_dashboard()

    def action_view_inconsistencies(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Inconsistencias Detectadas'),
            'res_model': 'data.correction.inconsistency',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'draft')],
        }

    def action_clear_all_inconsistencies(self):
        self.env['data.correction.inconsistency'].search([
            ('state', '=', 'draft')
        ]).unlink()
        return self._reload_dashboard()

    def _reload_dashboard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'data.correction.dashboard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'inline',
        }