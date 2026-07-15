# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DataCorrectionInconsistency(models.Model):
    _name = 'data.correction.inconsistency'
    _description = 'Inconsistencia de Datos o Impuestos'

    item_id = fields.Many2one('product.product', string='Ítem (Maestro)', required=True)
    source_model = fields.Selection([
        ('purchase', 'Compras'),
        ('pos', 'Ventas (PdV)'),
        ('sale', 'Ventas (Módulo de Ventas)'),
        ('inventory', 'Inventario')
    ], string='Origen', required=True)
    source_record_id = fields.Integer(string='ID de Registro Afectado')
    source_record_name = fields.Char(string='Referencia de Registro')
    field_to_correct = fields.Char(string='Campo a Corregir')
    old_value = fields.Char(string='Valor Anterior')
    new_value = fields.Char(string='Valor Nuevo Sugerido')
    precio_venta = fields.Float(string='Precio Venta Unitario')
    state = fields.Selection([
        ('draft', 'Pendiente'),
        ('corrected', 'Corregido'),
        ('ignored', 'Ignorado')
    ], string='Estado', default='draft')

    def action_apply_correction(self):
        # Lógica para aplicar corrección y generar historial
        for record in self:
            if record.state != 'draft':
                continue

            # Lógica específica para cada source_model y campo (actualmente enfocado en impuestos)
            try:
                if record.source_model == 'purchase' and record.field_to_correct == 'tax_ids':
                    line = self.env['account.move.line'].browse(record.source_record_id)
                    if line.exists() and line.move_id.state == 'draft':
                        taxes = line.product_id.supplier_taxes_id
                        line.write({'tax_ids': [(6, 0, taxes.ids)]})
                elif record.source_model == 'pos' and record.field_to_correct == 'tax_ids':
                    line = self.env['pos.order.line'].browse(record.source_record_id)
                    if line.exists():
                        taxes = line.product_id.taxes_id
                        
                        # Use SQL for POS to bypass Paid locks
                        self.env.cr.execute("DELETE FROM account_tax_pos_order_line_rel WHERE pos_order_line_id = %s", (line.id,))
                        for tax_id in taxes.ids:
                            self.env.cr.execute("INSERT INTO account_tax_pos_order_line_rel (pos_order_line_id, account_tax_id) VALUES (%s, %s)", (line.id, tax_id))
                            
                        # Si requiriese recomputo fiscal
                        if hasattr(line, 'tax_ids_after_fiscal_position'):
                            line.write({'tax_ids_after_fiscal_position': [(6, 0, taxes.ids)]})
                elif record.source_model == 'sale' and record.field_to_correct == 'tax_id':
                    line = self.env['sale.order.line'].browse(record.source_record_id)
                    if line.exists() and line.order_id.state in ['draft', 'sent']:
                        taxes = line.product_id.taxes_id
                        line.write({'tax_id': [(6, 0, taxes.ids)]})
                
                # --- Correcciones de Costo ---
                elif record.source_model == 'pos' and record.field_to_correct == 'Costo':
                    line = self.env['pos.order.line'].browse(record.source_record_id)
                    if line.exists():
                        new_cost = line.product_id.standard_price
                        if new_cost > 0:
                            if 'total_cost' in line._fields:
                                self.env.cr.execute("UPDATE pos_order_line SET total_cost = %s WHERE id = %s", (new_cost * line.qty, line.id))
                            elif 'margin' in line._fields:
                                # Fallback on older odoo versions or custom pos margin modules
                                self.env.cr.execute("UPDATE pos_order_line SET margin = %s WHERE id = %s", (line.price_subtotal - (new_cost * line.qty), line.id))
                            record.new_value = str(new_cost)
                        else:
                            raise ValueError("El costo maestro sigue siendo 0.00")
                            
                elif record.source_model == 'sale' and record.field_to_correct == 'Costo':
                    line = self.env['sale.order.line'].browse(record.source_record_id)
                    if line.exists():
                        new_cost = line.product_id.standard_price
                        if new_cost > 0:
                            if 'purchase_price' in line._fields:
                                self.env.cr.execute("UPDATE sale_order_line SET purchase_price = %s WHERE id = %s", (new_cost, line.id))
                                
                            # Fuerza a recalcular el margen si existe la función nativa
                            if hasattr(line, '_compute_margin'):
                                line._compute_margin()
                            record.new_value = str(new_cost)
                        else:
                            raise ValueError("El costo maestro sigue siendo 0.00")

            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Error aplicando corrección %s: %s", record.id, e)
                continue

            # Crear historial
            self.env['data.correction.history'].create({
                'fecha_correccion': fields.Datetime.now(),
                'usuario_id': self.env.user.id,
                'tipo_correccion': 'Corrección de ' + record.field_to_correct,
                'tabla_afectada': record.source_model,
                'id_registro_afectado': record.source_record_id,
                'campo_modificado': record.field_to_correct,
                'valor_anterior': record.old_value,
                'valor_nuevo': record.new_value,
            })
            record.state = 'corrected'

    def action_undo_correction(self):
        for record in self:
            if record.state != 'corrected':
                continue

            try:
                if record.field_to_correct == 'Costo':
                    try:
                        old_cost = float(record.old_value)
                    except ValueError:
                        old_cost = 0.0
                        
                    if record.source_model == 'pos':
                        line = self.env['pos.order.line'].browse(record.source_record_id)
                        if line.exists():
                            if 'total_cost' in line._fields:
                                self.env.cr.execute("UPDATE pos_order_line SET total_cost = %s WHERE id = %s", (old_cost * line.qty, line.id))
                            elif 'margin' in line._fields:
                                self.env.cr.execute("UPDATE pos_order_line SET margin = %s WHERE id = %s", (line.price_subtotal - (old_cost * line.qty), line.id))
                    
                    elif record.source_model == 'sale':
                        line = self.env['sale.order.line'].browse(record.source_record_id)
                        if line.exists():
                            if 'purchase_price' in line._fields:
                                self.env.cr.execute("UPDATE sale_order_line SET purchase_price = %s WHERE id = %s", (old_cost, line.id))
                            if hasattr(line, '_compute_margin'):
                                line._compute_margin()

                elif record.field_to_correct in ['tax_ids', 'tax_id']:
                    taxes_to_set = []
                    if record.old_value and record.old_value != 'Sin impuestos':
                        tax_names = record.old_value.split(', ')
                        type_tax_use = 'purchase' if record.source_model == 'purchase' else 'sale'
                        found_taxes = self.env['account.tax'].search([('name', 'in', tax_names), ('type_tax_use', '=', type_tax_use)])
                        if found_taxes:
                            taxes_to_set = [(6, 0, found_taxes.ids)]
                    else:
                        taxes_to_set = [(5, 0, 0)]

                    if record.source_model == 'purchase':
                        line = self.env['account.move.line'].browse(record.source_record_id)
                        if line.exists() and line.move_id.state == 'draft':
                            line.write({'tax_ids': taxes_to_set})
                            
                    elif record.source_model == 'pos':
                        line = self.env['pos.order.line'].browse(record.source_record_id)
                        if line.exists():
                            self.env.cr.execute("DELETE FROM account_tax_pos_order_line_rel WHERE pos_order_line_id = %s", (line.id,))
                            if taxes_to_set and taxes_to_set[0][0] == 6:
                                for tax_id in taxes_to_set[0][2]:
                                    self.env.cr.execute("INSERT INTO account_tax_pos_order_line_rel (pos_order_line_id, account_tax_id) VALUES (%s, %s)", (line.id, tax_id))
                                    
                    elif record.source_model == 'sale':
                        line = self.env['sale.order.line'].browse(record.source_record_id)
                        if line.exists() and line.order_id.state in ['draft', 'sent']:
                            line.write({'tax_id': taxes_to_set})

            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Error deshaciendo corrección %s: %s", record.id, e)
                continue

            record.write({'state': 'draft'})
            
            self.env['data.correction.history'].create({
                'fecha_correccion': fields.Datetime.now(),
                'usuario_id': self.env.user.id,
                'tipo_correccion': 'Reversión de ' + record.field_to_correct,
                'tabla_afectada': record.source_model,
                'id_registro_afectado': record.source_record_id,
                'campo_modificado': record.field_to_correct,
                'valor_anterior': record.new_value,
                'valor_nuevo': record.old_value,
            })

    def action_ignore(self):
        self.write({'state': 'ignored'})
