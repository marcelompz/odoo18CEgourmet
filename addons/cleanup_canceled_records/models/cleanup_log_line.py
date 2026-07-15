# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json


class CleanupLogLine(models.Model):
    _name = 'cleanup.log.line'
    _description = 'Cleanup Log Line'
    _order = 'log_id desc, model_name, record_id'
    
    log_id = fields.Many2one('cleanup.log', string='Cleanup Log', required=True, ondelete='cascade')
    execution_date = fields.Datetime(string='Execution Date', related='log_id.execution_date', store=True, readonly=True)
    
    # Información del registro
    model_name = fields.Char(string='Model', required=True, readonly=True)
    model_description = fields.Char(string='Model Description', readonly=True)
    record_id = fields.Integer(string='Record ID', required=True, readonly=True)
    record_name = fields.Char(string='Record Name', readonly=True)
    
    # Usuario original (quien cometió el error)
    original_user_id = fields.Many2one('res.users', string='Original User', readonly=True)
    original_create_date = fields.Datetime(string='Original Create Date', readonly=True)
    
    # Tipo de acción
    action_type = fields.Selection([
        ('cancel', 'Cancel'),
        ('delete', 'Delete'),
        ('state_change', 'State Change'),
        ('tax_correction', 'Tax Correction'),
        ('tax_assignment', 'Tax Assignment'),
        ('field_update', 'Field Update'),
        ('relation_update', 'Relation Update'),
    ], string='Action Type', required=True, readonly=True)
    
    # Valores antes/después
    old_values = fields.Text(string='Old Values', readonly=True,
        help='JSON representation of field values before cleanup')
    new_values = fields.Text(string='New Values', readonly=True,
        help='JSON representation of field values after cleanup')
    
    # Información específica para corrección de impuestos POS
    product_id = fields.Many2one('product.product', string='Product', readonly=True, ondelete='set null')
    pos_order_line_id = fields.Many2one('pos.order.line', string='POS Order Line', readonly=True, ondelete='set null')
    pos_order_id = fields.Many2one('pos.order', string='POS Order', readonly=True, ondelete='set null')
    
    expected_tax_ids = fields.Many2many('account.tax', string='Expected Taxes', readonly=True,
        relation='cleanup_log_line_expected_tax_rel',
        column1='log_line_id', column2='tax_id')
    applied_tax_ids = fields.Many2many('account.tax', string='Applied Taxes', readonly=True,
        relation='cleanup_log_line_applied_tax_rel',
        column1='log_line_id', column2='tax_id')
    
    discrepancy_type = fields.Selection([
        ('missing', 'Missing Tax'),
        ('incorrect', 'Incorrect Tax'),
        ('extra', 'Extra Tax'),
        ('rate_mismatch', 'Tax Rate Mismatch'),
    ], string='Discrepancy Type', readonly=True)
    
    # Información financiera
    price_subtotal_before = fields.Float(string='Subtotal Before', readonly=True)
    price_subtotal_after = fields.Float(string='Subtotal After', readonly=True)
    price_total_before = fields.Float(string='Total Before', readonly=True)
    price_total_after = fields.Float(string='Total After', readonly=True)
    tax_amount_before = fields.Float(string='Tax Amount Before', readonly=True)
    tax_amount_after = fields.Float(string='Tax Amount After', readonly=True)
    
    # Estado
    status = fields.Selection([
        ('pending', 'Pending'),
        ('applied', 'Applied'),
        ('failed', 'Failed'),
        ('reverted', 'Reverted'),
    ], string='Status', default='pending', readonly=True)
    
    error_message = fields.Text(string='Error Message', readonly=True)
    
    # Métodos
    def name_get(self):
        result = []
        for line in self:
            name = f"{line.model_name}:{line.record_id}"
            if line.record_name:
                name = f"{name} ({line.record_name})"
            result.append((line.id, name))
        return result
    
    def _get_old_value(self, field_name):
        """Obtener valor antiguo de un campo específico"""
        self.ensure_one()
        if not self.old_values:
            return None
        try:
            values = json.loads(self.old_values)
            return values.get(field_name)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def _get_new_value(self, field_name):
        """Obtener valor nuevo de un campo específico"""
        self.ensure_one()
        if not self.new_values:
            return None
        try:
            values = json.loads(self.new_values)
            return values.get(field_name)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def action_view_record(self):
        """Abrir el registro original"""
        self.ensure_one()
        
        if not self.model_name or not self.record_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Cannot open record: missing model or ID'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        try:
            model = self.env[self.model_name]
            record = model.browse(self.record_id)
            
            if not record.exists():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _('Record no longer exists'),
                        'type': 'warning',
                        'sticky': False,
                    }
                }
            
            return {
                'type': 'ir.actions.act_window',
                'name': record.display_name or _('Record'),
                'res_model': self.model_name,
                'res_id': self.record_id,
                'view_mode': 'form',
                'target': 'current',
            }
        except KeyError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Invalid model: %s') % self.model_name,
                    'type': 'warning',
                    'sticky': False,
                }
            }
    
    def _create_log_line(self, log_id, model, record, action_type, old_vals, new_vals, **kwargs):
        """Método helper para crear líneas de log"""
        # Obtener nombre del registro de manera segura
        record_name = str(record.id)
        try:
            if hasattr(record, 'display_name') and record.display_name:
                record_name = record.display_name
            elif hasattr(record, 'name') and record.name:
                record_name = record.name
            elif hasattr(record, 'reference') and record.reference:
                record_name = record.reference
            elif hasattr(record, 'name_get'):
                # Último recurso: usar name_get si existe
                name_result = record.name_get()
                if name_result and len(name_result) > 0:
                    record_name = name_result[0][1]
        except Exception:
            # Si algo falla, mantener el ID como nombre
            record_name = str(record.id)
        
        values = {
            'log_id': log_id,
            'model_name': model._name,
            'model_description': model._description,
            'record_id': record.id,
            'record_name': record_name,
            'action_type': action_type,
            'old_values': json.dumps(old_vals) if old_vals else None,
            'new_values': json.dumps(new_vals) if new_vals else None,
            'status': 'applied',
        }
        
        # Capturar usuario original si está disponible
        if hasattr(record, 'create_uid'):
            values['original_user_id'] = record.create_uid.id
        if hasattr(record, 'create_date'):
            values['original_create_date'] = record.create_date
        
        # Campos específicos para POS
        if model._name == 'pos.order.line':
            values.update({
                'product_id': record.product_id.id,
                'pos_order_line_id': record.id,
                'pos_order_id': record.order_id.id,
            })
        
        # Actualizar con kwargs adicionales
        values.update(kwargs)
        
        return self.create(values)
    
    def _revert(self):
        """Revert the change recorded in this log line"""
        self.ensure_one()
        
        if self.status == 'reverted':
            raise UserError(_('This change has already been reverted.'))
        
        if not self.old_values:
            raise UserError(_('No old values stored for this change.'))
        
        try:
            old_vals = json.loads(self.old_values)
        except json.JSONDecodeError:
            raise UserError(_('Invalid old values format.'))
        
        model = self.env[self.model_name]
        
        # Handle different action types
        if self.action_type == 'delete':
            # Cannot recreate deleted records with basic info
            # Just mark as reverted
            self.write({'status': 'reverted'})
            return True
        
        # Check if record still exists
        record = model.browse(self.record_id)
        if not record.exists():
            # Record was deleted, cannot revert
            self.write({'status': 'reverted'})
            return True
        
        # Apply old values based on action type
        if self.action_type in ['state_change', 'field_update', 'tax_correction']:
            # For tax correction, need to convert tax_ids list to command tuple
            if self.action_type == 'tax_correction' and 'tax_ids' in old_vals:
                old_vals = {'tax_ids': [(6, 0, old_vals['tax_ids'])]}
            
            record.write(old_vals)
            self.write({'status': 'reverted'})
            return True
        
        # For cancel actions, revert state to original
        if self.action_type == 'cancel':
            if 'state' in old_vals:
                record.write({'state': old_vals['state']})
                self.write({'status': 'reverted'})
                return True
        
        # Default: mark as reverted
        self.write({'status': 'reverted'})
        return True