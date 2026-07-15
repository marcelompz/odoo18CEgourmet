# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CleanupLog(models.Model):
    _name = 'cleanup.log'
    _description = 'Cleanup Log'
    _order = 'execution_date desc'
    _rec_name = 'name'
    
    name = fields.Char(string='Reference', readonly=True, default=lambda self: _('New'))
    execution_date = fields.Datetime(string='Execution Date', readonly=True, default=fields.Datetime.now)
    executed_by = fields.Many2one('res.users', string='Executed By', readonly=True, default=lambda self: self.env.user)
    
    # Configuración utilizada
    config_id = fields.Many2one('cleanup.config', string='Configuration', readonly=True)
    cleanup_type = fields.Selection([
        ('all', 'All Types'),
        ('purchase', 'Purchases Only'),
        ('pos', 'POS Only'),
        ('stock', 'Inventory Only'),
        ('account', 'Invoices Only'),
    ], string='Cleanup Type', readonly=True)
    
    # Resultados generales
    status = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('partially_reverted', 'Partially Reverted'),
        ('reverted', 'Reverted'),
    ], string='Status', default='draft', readonly=True)
    
    total_processed = fields.Integer(string='Total Processed', readonly=True)
    total_corrected = fields.Integer(string='Total Corrected', readonly=True)
    total_failed = fields.Integer(string='Total Failed', readonly=True)
    
    # Desglose por modelo
    stock_moves_processed = fields.Integer(string='Stock Moves Processed', readonly=True)
    stock_moves_corrected = fields.Integer(string='Stock Moves Corrected', readonly=True)
    
    purchase_orders_processed = fields.Integer(string='Purchase Orders Processed', readonly=True)
    purchase_orders_corrected = fields.Integer(string='Purchase Orders Corrected', readonly=True)
    
    account_moves_processed = fields.Integer(string='Account Moves Processed', readonly=True)
    account_moves_corrected = fields.Integer(string='Account Moves Corrected', readonly=True)
    
    pos_orders_processed = fields.Integer(string='POS Orders Processed', readonly=True)
    pos_lines_processed = fields.Integer(string='POS Lines Processed', readonly=True)
    pos_lines_corrected = fields.Integer(string='POS Lines Corrected', readonly=True)
    
    # Información de reversión
    reverted = fields.Boolean(string='Reverted', readonly=True)
    reverted_by = fields.Many2one('res.users', string='Reverted By', readonly=True)
    revert_date = fields.Datetime(string='Revert Date', readonly=True)
    revert_reason = fields.Text(string='Revert Reason', readonly=True)
    
    # Errores y advertencias
    error_log = fields.Text(string='Error Log', readonly=True)
    warning_log = fields.Text(string='Warning Log', readonly=True)
    
    # Líneas detalladas
    log_line_ids = fields.One2many('cleanup.log.line', 'log_id', string='Detailed Log Lines', readonly=True)
    
    # Métodos
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
            vals['name'] = self.env['ir.sequence'].next_by_code('cleanup.log', sequence_date=seq_date) or _('New')
        return super(CleanupLog, self).create(vals)
    
    def action_view_log_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Log Lines'),
            'res_model': 'cleanup.log.line',
            'view_mode': 'tree,form',
            'domain': [('log_id', '=', self.id)],
            'context': {'default_log_id': self.id},
        }
    
    def action_revert(self):
        self.ensure_one()
        
        # Crear wizard de reversión
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revert Cleanup'),
            'res_model': 'cleanup.revert.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_log_id': self.id},
        }
    
    def action_export_log(self):
        self.ensure_one()
        # Implementar exportación CSV
        return {
            'type': 'ir.actions.act_window',
            'name': _('Export Log'),
            'res_model': 'cleanup.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_log_id': self.id},
        }
    
    def _update_status(self, new_status):
        self.write({'status': new_status})
    
    def _add_error(self, error_message):
        self.write({
            'error_log': (self.error_log or '') + f"{fields.Datetime.now()}: {error_message}\n"
        })
    
    def _add_warning(self, warning_message):
        self.write({
            'warning_log': (self.warning_log or '') + f"{fields.Datetime.now()}: {warning_message}\n"
        })