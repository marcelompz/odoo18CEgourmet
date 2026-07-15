# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json


class CleanupRevertWizard(models.TransientModel):
    _name = 'cleanup.revert.wizard'
    _description = 'Cleanup Revert Wizard'
    
    log_id = fields.Many2one('cleanup.log', string='Cleanup Log', required=True, readonly=True)
    
    # Options
    revert_type = fields.Selection([
        ('all', 'Revert All Changes'),
        ('selected', 'Revert Selected Lines Only'),
    ], string='Revert Type', default='all', required=True)
    
    revert_action = fields.Selection([
        ('restore', 'Restore Original Values'),
        ('keep_current', 'Keep Current Values (Mark as Reverted)'),
    ], string='Revert Action', default='restore', required=True,
       help="Restore Original Values: Apply old values from log. Keep Current Values: Only mark log as reverted without changing data.")
    
    # Lines selection
    line_ids = fields.One2many('cleanup.revert.wizard.line', 'wizard_id', string='Lines to Revert')
    
    # Results
    state = fields.Selection([
        ('config', 'Configuration'),
        ('selection', 'Selection'),
        ('execution', 'Execution'),
        ('results', 'Results'),
    ], string='State', default='config')
    
    lines_processed = fields.Integer(string='Lines Processed', readonly=True)
    lines_reverted = fields.Integer(string='Lines Reverted', readonly=True)
    lines_failed = fields.Integer(string='Lines Failed', readonly=True)
    error_log = fields.Text(string='Error Log', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        defaults = super(CleanupRevertWizard, self).default_get(fields_list)
        context = self.env.context
        
        if 'default_log_id' in context:
            log_id = context['default_log_id']
            log = self.env['cleanup.log'].browse(log_id)
            if log.exists():
                defaults['log_id'] = log.id
                
                # Create wizard lines for each log line
                line_vals = []
                for log_line in log.log_line_ids.filtered(lambda l: l.status == 'applied'):
                    line_vals.append((0, 0, {
                        'log_line_id': log_line.id,
                        'model_name': log_line.model_name,
                        'record_id': log_line.record_id,
                        'record_name': log_line.record_name,
                        'action_type': log_line.action_type,
                        'selected': True,
                    }))
                defaults['line_ids'] = line_vals
                defaults['state'] = 'selection'
        
        return defaults
    
    def action_revert(self):
        self.ensure_one()
        
        lines_to_revert = self.line_ids.filtered(lambda l: l.selected)
        if self.revert_type == 'all':
            lines_to_revert = self.line_ids
        
        if not lines_to_revert:
            raise UserError(_('No lines selected for revert.'))
        
        self.write({'state': 'execution'})
        
        processed = 0
        reverted = 0
        failed = 0
        errors = []
        
        for wizard_line in lines_to_revert:
            log_line = wizard_line.log_line_id
            
            try:
                if self.revert_action == 'restore':
                    success = log_line._revert()
                else:
                    # Just mark as reverted
                    log_line.write({'status': 'reverted'})
                    success = True
                
                if success:
                    reverted += 1
                else:
                    failed += 1
                    errors.append(_('Failed to revert line %s (ID: %s)') % (log_line.record_name, log_line.record_id))
                
                processed += 1
                
            except Exception as e:
                failed += 1
                processed += 1
                errors.append(_('Error reverting line %s: %s') % (log_line.record_name, str(e)))
        
        # Update log status
        if reverted > 0:
            all_log_lines = self.log_id.log_line_ids
            if all(all_log_lines.mapped(lambda l: l.status == 'reverted')):
                self.log_id.write({
                    'status': 'reverted',
                    'reverted': True,
                    'reverted_by': self.env.user.id,
                    'revert_date': fields.Datetime.now(),
                })
            else:
                self.log_id.write({
                    'status': 'partially_reverted',
                    'reverted_by': self.env.user.id,
                    'revert_date': fields.Datetime.now(),
                })
        
        self.write({
            'state': 'results',
            'lines_processed': processed,
            'lines_reverted': reverted,
            'lines_failed': failed,
            'error_log': '\n'.join(errors) if errors else '',
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Revert Completed'),
                'message': _('Reverted %s lines, %s failed.') % (reverted, failed),
                'sticky': False,
            }
        }
    
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class CleanupRevertWizardLine(models.TransientModel):
    _name = 'cleanup.revert.wizard.line'
    _description = 'Cleanup Revert Wizard Line'
    
    wizard_id = fields.Many2one('cleanup.revert.wizard', string='Wizard', required=True, ondelete='cascade')
    log_line_id = fields.Many2one('cleanup.log.line', string='Log Line', required=True, ondelete='cascade')
    
    selected = fields.Boolean(string='Selected', default=True)
    
    model_name = fields.Char(string='Model', readonly=True)
    record_id = fields.Integer(string='Record ID', readonly=True)
    record_name = fields.Char(string='Record Name', readonly=True)
    action_type = fields.Selection([
        ('cancel', 'Cancel'),
        ('delete', 'Delete'),
        ('state_change', 'State Change'),
        ('tax_correction', 'Tax Correction'),
        ('field_update', 'Field Update'),
        ('relation_update', 'Relation Update'),
    ], string='Action Type', readonly=True)