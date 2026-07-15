# -*- coding: utf-8 -*-
import logging, traceback
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json

_logger = logging.getLogger(__name__)


class CleanupPosTaxWizard(models.TransientModel):
    _name = 'cleanup.pos.tax.wizard'
    _description = 'POS Tax Correction Wizard'
    
    config_id = fields.Many2one('cleanup.config', string='Configuration', required=True, default=lambda self: self.env.context.get('default_config_id'))
    
    # Override options
    pos_tax_action = fields.Selection([
        ('report', 'Only Report'),
        ('correct', 'Correct Automatically'),
        ('cancel', 'Cancel Orders with Errors'),
    ], string='Action', required=True)
    
    # Filters
    pos_date_from = fields.Date(string='Date From')
    pos_date_to = fields.Date(string='Date To')
    
    # Progress
    state = fields.Selection([
        ('config', 'Configuration'),
        ('detection', 'Detection'),
        ('validation', 'Validation'),
        ('execution', 'Execution'),
        ('results', 'Results'),
    ], string='State', default='config')
    
    # Detection results
    total_lines_detected = fields.Integer(string='Total Lines Detected', readonly=True)
    missing_tax_count = fields.Integer(string='Missing Taxes', readonly=True)
    incorrect_tax_count = fields.Integer(string='Incorrect Taxes', readonly=True)
    extra_tax_count = fields.Integer(string='Extra Taxes', readonly=True)
    
    # Validation lines
    validation_line_ids = fields.One2many('cleanup.pos.tax.validation.line', 'wizard_id', string='Validation Lines')
    
    # Execution results
    lines_processed = fields.Integer(string='Lines Processed', readonly=True)
    lines_corrected = fields.Integer(string='Lines Corrected', readonly=True)
    lines_failed = fields.Integer(string='Lines Failed', readonly=True)
    error_log = fields.Text(string='Error Log', readonly=True)
    
    # Log reference
    log_id = fields.Many2one('cleanup.log', string='Log Reference', readonly=True)
    
    # Methods
    @api.onchange('config_id')
    def _onchange_config_id(self):
        if self.config_id:
            self.pos_tax_action = self.config_id.pos_tax_action
            self.pos_date_from = self.config_id.pos_date_from
            self.pos_date_to = self.config_id.pos_date_to

    @api.model
    def create(self, vals):
        try:
            return super(CleanupPosTaxWizard, self).create(vals)
        except Exception as e:
            _logger.error("Error creating POS tax wizard: %s\n%s", e, traceback.format_exc())
            raise
    
    def action_detect_issues(self):
        """Detect POS tax issues based on current configuration"""
        self.ensure_one()
        
        # Check if POS module is available
        if not self.config_id._is_pos_available():
            raise UserError(_('The Point of Sale module is not installed or not available. Please install the point_of_sale module to use POS tax corrections.'))
        
        # Update filters from wizard
        if self.pos_date_from:
            self.config_id.write({'pos_date_from': self.pos_date_from})
        if self.pos_date_to:
            self.config_id.write({'pos_date_to': self.pos_date_to})
        
        # Detect issues using config method
        issues = self.config_id._detect_pos_tax_issues()
        
        # Clear existing validation lines
        self.validation_line_ids.unlink()
        
        # Create validation lines
        ValidationLine = self.env['cleanup.pos.tax.validation.line']
        validation_lines = []
        
        _logger.info("Processing %s POS tax issues", len(issues))
        
        for idx, issue in enumerate(issues):
            try:
                # Filter out None values from tax IDs and convert to integers
                expected_tax_ids = issue.get('expected_tax_ids') or []
                applied_tax_ids = issue.get('applied_tax_ids') or []
                
                # Ensure we have lists
                if not isinstance(expected_tax_ids, list):
                    expected_tax_ids = []
                if not isinstance(applied_tax_ids, list):
                    applied_tax_ids = []
                
                # Clean and convert tax IDs
                filtered_expected = []
                for tid in expected_tax_ids:
                    if tid is None:
                        continue
                    try:
                        tid_int = int(tid)
                        filtered_expected.append(tid_int)
                    except (ValueError, TypeError):
                        _logger.warning("Invalid tax ID in expected_tax_ids: %s", tid)
                
                filtered_applied = []
                for tid in applied_tax_ids:
                    if tid is None:
                        continue
                    try:
                        tid_int = int(tid)
                        filtered_applied.append(tid_int)
                    except (ValueError, TypeError):
                        _logger.warning("Invalid tax ID in applied_tax_ids: %s", tid)
                
                # Log if we found any issues with tax IDs
                if len(expected_tax_ids) != len(filtered_expected) or len(applied_tax_ids) != len(filtered_applied):
                    _logger.debug("Filtered tax IDs for issue %s: expected %s->%s, applied %s->%s", 
                                 idx, len(expected_tax_ids), len(filtered_expected),
                                 len(applied_tax_ids), len(filtered_applied))
                
                line_vals = {
                    'wizard_id': self.id,
                    'pos_order_line_id': issue['line_id'],
                    'product_id': issue['product_id'],
                    'order_id': issue['order_id'],
                    'expected_tax_ids': [(6, 0, filtered_expected)],
                    'current_tax_ids': [(6, 0, filtered_applied)],
                    'discrepancy_type': issue.get('discrepancy_type', 'unknown'),
                    'price_subtotal': issue.get('price_subtotal', 0.0),
                    'current_total': issue.get('price_subtotal_incl', 0.0),
                }
                validation_lines.append((0, 0, line_vals))
                
            except Exception as e:
                _logger.error("Error processing POS tax issue %s: %s", idx, str(e))
                # Continue with next issue
        
        # Update counts
        missing_count = len([i for i in issues if i['discrepancy_type'] == 'missing'])
        incorrect_count = len([i for i in issues if i['discrepancy_type'] == 'incorrect'])
        extra_count = len([i for i in issues if i['discrepancy_type'] == 'extra'])
        
        self.write({
            'state': 'validation',
            'total_lines_detected': len(issues),
            'missing_tax_count': missing_count,
            'incorrect_tax_count': incorrect_count,
            'extra_tax_count': extra_count,
            'validation_line_ids': validation_lines,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_select_all(self):
        """Select all validation lines"""
        self.ensure_one()
        self.validation_line_ids.write({'selected': True})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_deselect_all(self):
        """Deselect all validation lines"""
        self.ensure_one()
        self.validation_line_ids.write({'selected': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_calculate_totals(self):
        """Calculate new totals for selected lines"""
        self.ensure_one()
        
        selected_lines = self.validation_line_ids.filtered(lambda l: l.selected)
        
        for line in selected_lines:
            line._calculate_new_totals()
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_execute_corrections(self):
        """Execute corrections for selected lines"""
        self.ensure_one()
        
        selected_lines = self.validation_line_ids.filtered(lambda l: l.selected)
        if not selected_lines:
            raise UserError(_('Please select at least one line to correct'))
        
        # Create log if enabled
        log = None
        if self.config_id.enable_logging:
            log = self.config_id._create_cleanup_log()
            self.log_id = log.id
        
        lines_processed = 0
        lines_corrected = 0
        lines_failed = 0
        error_messages = []
        
        for line in selected_lines:
            try:
                # Prepare issue dict for correction
                issue = {
                    'line_id': line.pos_order_line_id.id,
                    'product_id': line.product_id.id,
                    'order_id': line.order_id.id,
                    'expected_tax_ids': line.expected_tax_ids.ids,
                    'applied_tax_ids': line.current_tax_ids.ids,
                    'discrepancy_type': line.discrepancy_type,
                    'price_subtotal': line.price_subtotal,
                    'price_subtotal_incl': line.current_total,
                }
                
                # Call correction method
                LogLine = self.env['cleanup.log.line']
                corrected = self.config_id._correct_pos_tax_issue(log.id if log else False, issue, LogLine)
                
                if corrected:
                    lines_corrected += 1
                    line.write({'status': 'corrected'})
                else:
                    lines_failed += 1
                    line.write({'status': 'failed', 'error_message': _('Unknown error')})
                
                lines_processed += 1
                
            except Exception as e:
                lines_failed += 1
                lines_processed += 1
                error_messages.append(f"Line {line.id}: {str(e)}")
                line.write({'status': 'failed', 'error_message': str(e)})
        
        # Update log if exists
        if log:
            log.write({
                'status': 'completed',
                'total_processed': lines_processed,
                'total_corrected': lines_corrected,
                'pos_lines_processed': lines_processed,
                'pos_lines_corrected': lines_corrected,
                'error_log': '\n'.join(error_messages) if error_messages else False,
            })
        
        # Update wizard
        self.write({
            'state': 'results',
            'lines_processed': lines_processed,
            'lines_corrected': lines_corrected,
            'lines_failed': lines_failed,
            'error_log': '\n'.join(error_messages) if error_messages else '',
        })
        
        # Update config results
        self.config_id.write({
            'pos_lines_processed': lines_processed,
            'pos_lines_corrected': lines_corrected,
            'last_log_id': log.id if log else False,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_view_log(self):
        """View the created log"""
        self.ensure_one()
        if not self.log_id:
            raise UserError(_('No log available'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cleanup Log'),
            'res_model': 'cleanup.log',
            'res_id': self.log_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_back_to_config(self):
        """Go back to configuration step"""
        self.ensure_one()
        self.write({'state': 'config'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}


class CleanupPosTaxValidationLine(models.TransientModel):
    _name = 'cleanup.pos.tax.validation.line'
    _description = 'POS Tax Validation Line'
    _order = 'order_id, product_id'
    
    wizard_id = fields.Many2one('cleanup.pos.tax.wizard', string='Wizard', required=True, ondelete='cascade')
    
    # Record information
    pos_order_line_id = fields.Many2one('pos.order.line', string='POS Line', required=False, readonly=True)
    product_id = fields.Many2one('product.product', string='Product', required=False, readonly=True)
    order_id = fields.Many2one('pos.order', string='Order', readonly=True)
    
    # Tax information
    expected_tax_ids = fields.Many2many('account.tax', 
        relation='cleanup_pos_tax_validation_expected_rel',
        column1='validation_line_id',
        column2='tax_id',
        string='Expected Taxes', readonly=True)
    current_tax_ids = fields.Many2many('account.tax', 
        relation='cleanup_pos_tax_validation_current_rel',
        column1='validation_line_id',
        column2='tax_id',
        string='Current Taxes', readonly=True)
    discrepancy_type = fields.Selection([
        ('missing', 'Missing Tax'),
        ('incorrect', 'Incorrect Tax'),
        ('extra', 'Extra Tax'),
    ], string='Discrepancy Type', readonly=True)
    
    # Financial information
    price_subtotal = fields.Float(string='Subtotal', readonly=True)
    current_total = fields.Float(string='Current Total', readonly=True)
    calculated_total = fields.Float(string='Calculated Total', readonly=True)
    difference = fields.Float(string='Difference', readonly=True)
    
    # Action
    selected = fields.Boolean(string='Select', default=True)
    action = fields.Selection([
        ('correct', 'Correct'),
        ('ignore', 'Ignore'),
        ('cancel', 'Cancel Line'),
    ], string='Action', default='correct')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('corrected', 'Corrected'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ], string='Status', default='pending', readonly=True)
    
    error_message = fields.Text(string='Error Message', readonly=True)
    
    # Methods
    def name_get(self):
        result = []
        for line in self:
            name = f"{line.order_id.name or 'Order'}: {line.product_id.display_name}"
            result.append((line.id, name))
        return result
    
    def _calculate_new_totals(self):
        """Calculate new totals based on expected taxes"""
        self.ensure_one()
        
        if not self.expected_tax_ids:
            # No taxes expected, total = subtotal
            calculated_total = self.price_subtotal
        else:
            # Calculate tax amount
            price_unit = self.price_subtotal / (self.pos_order_line_id.qty or 1)
            taxes_computed = self.expected_tax_ids.compute_all(
                price_unit,
                currency=self.pos_order_line_id.currency_id,
                quantity=self.pos_order_line_id.qty
            )
            tax_amount = sum(tax.get('amount', 0) for tax in taxes_computed.get('taxes', []))
            calculated_total = self.price_subtotal + tax_amount
        
        difference = calculated_total - self.current_total
        
        self.write({
            'calculated_total': calculated_total,
            'difference': difference,
        })
        
        return True
    
    def action_view_line(self):
        """View the POS order line"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('POS Order Line'),
            'res_model': 'pos.order.line',
            'res_id': self.pos_order_line_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_order(self):
        """View the POS order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('POS Order'),
            'res_model': 'pos.order',
            'res_id': self.order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }