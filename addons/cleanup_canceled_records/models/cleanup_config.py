# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CleanupConfig(models.Model):
    _name = 'cleanup.config'
    _description = 'Cleanup Configuration'
    
    name = fields.Char(string='Name', required=True, default='Cleanup Configuration')
    active = fields.Boolean(string='Active', default=True)
    
    # Model selection
    cleanup_stock_moves = fields.Boolean(string='Cleanup Stock Moves', default=True)
    cleanup_purchase_orders = fields.Boolean(string='Cleanup Purchase Orders', default=True)
    cleanup_account_moves = fields.Boolean(string='Cleanup Account Moves', default=True)
    
    # State selection
    stock_move_states = fields.Selection([
        ('cancel', 'Canceled Only'),
        ('blocked', 'Blocked (Done) Only'),
        ('both', 'Both Canceled and Blocked'),
        ('all', 'All States'),
    ], string='Stock Move States', default='cancel', required=True)
    
    purchase_order_states = fields.Selection([
        ('cancel', 'Canceled Only'),
        ('blocked', 'Blocked (Done) Only'),
        ('both', 'Both Canceled and Blocked'),
        ('all', 'All States'),
    ], string='Purchase Order States', default='cancel', required=True)
    
    account_move_states = fields.Selection([
        ('cancel', 'Canceled Only'),
        ('blocked', 'Blocked (Posted) Only'),
        ('both', 'Both Canceled and Blocked'),
        ('all', 'All States'),
    ], string='Account Move States', default='cancel', required=True)
    
    # Cleanup type selection
    cleanup_type = fields.Selection([
        ('all', 'All Types'),
        ('purchase', 'Purchases Only'),
        ('pos', 'POS Only'),
        ('stock', 'Inventory Only'),
        ('account', 'Invoices Only'),
    ], string='Cleanup Type', default='all', required=True)
    
    # POS Tax Correction
    cleanup_pos_taxes = fields.Boolean(string='Correct POS Taxes', default=True)
    pos_tax_correction_type = fields.Selection([
        ('missing', 'Only Missing Taxes'),
        ('incorrect', 'Only Incorrect Taxes'),
        ('both', 'Both Missing and Incorrect'),
        ('all', 'All POS Lines'),
    ], string='POS Tax Correction Type', default='both', required=True)
    
    pos_tax_action = fields.Selection([
        ('report', 'Only Report'),
        ('correct', 'Correct Automatically'),
        ('cancel', 'Cancel Orders with Errors'),
    ], string='POS Tax Action', default='report', required=True)
    
    pos_default_tax_id = fields.Many2one('account.tax',
        string='Default Tax',
        domain=[('type_tax_use', '=', 'sale')],
        help='Tax to apply when product has no tax configuration')
    
    # Date range for POS
    pos_date_from = fields.Date(string='POS Date From')
    pos_date_to = fields.Date(string='POS Date To')
    
    # Logging and audit
    enable_logging = fields.Boolean(string='Enable Detailed Logging', default=True,
        help='Store detailed log of all changes for audit and revert capability')
    enable_revert = fields.Boolean(string='Enable Revert Function', default=True,
        help='Allow reverting changes made by cleanup operations')
    
    # Action
    action_type = fields.Selection([
        ('cancel', 'Only Cancel'),
        ('delete', 'Delete Permanently'),
        ('cancel_delete', 'Cancel then Delete'),
    ], string='Action Type', default='cancel', required=True)
    
    # Date range
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    
    # Results
    last_execution = fields.Datetime(string='Last Execution')
    stock_moves_processed = fields.Integer(string='Stock Moves Processed', readonly=True)
    purchase_orders_processed = fields.Integer(string='Purchase Orders Processed', readonly=True)
    account_moves_processed = fields.Integer(string='Account Moves Processed', readonly=True)
    
    # POS Results
    pos_orders_processed = fields.Integer(string='POS Orders Processed', readonly=True)
    pos_lines_processed = fields.Integer(string='POS Lines Processed', readonly=True)
    pos_lines_corrected = fields.Integer(string='POS Lines Corrected', readonly=True)
    
    # Log reference
    last_log_id = fields.Many2one('cleanup.log', string='Last Log', readonly=True)
    
    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise ValidationError(_('Date From cannot be greater than Date To'))
    
    @api.constrains('pos_date_from', 'pos_date_to')
    def _check_pos_date_range(self):
        for record in self:
            if record.pos_date_from and record.pos_date_to and record.pos_date_from > record.pos_date_to:
                raise ValidationError(_('POS Date From cannot be greater than POS Date To'))
    
    # Helper methods
    def _create_cleanup_log(self):
        """Create a new cleanup log record"""
        log_vals = {
            'config_id': self.id,
            'cleanup_type': self.cleanup_type,
            'status': 'running',
        }
        return self.env['cleanup.log'].create(log_vals)
    
    def _log_record_change(self, log_id, record, action_type, old_vals, new_vals, **kwargs):
        """Create a log line for a record change"""
        if not log_id:
            return None
        
        LogLine = self.env['cleanup.log.line']
        model = self.env[record._name]
        log_line = LogLine._create_log_line(
            log_id=log_id,
            model=model,
            record=record,
            action_type=action_type,
            old_vals=old_vals,
            new_vals=new_vals,
            **kwargs
        )
        return log_line
    
    def _is_pos_available(self):
        """Check if POS module is installed and models are available"""
        try:
            # Check if pos.order model exists in registry
            return bool(self.env.get('pos.order') and self.env.get('pos.order.line'))
        except Exception:
            return False
    
    def _validate_pos_config(self):
        """Validate POS configuration before opening wizard"""
        self.ensure_one()
        if not self._is_pos_available():
            raise ValidationError(_('The Point of Sale module is not installed or not available. Please install the point_of_sale module to use POS tax corrections.'))
        if not self.cleanup_pos_taxes:
            raise ValidationError(_('POS tax correction is not enabled in this configuration. Please enable "Correct POS Taxes" in the POS Tax Correction tab.'))
        if self.cleanup_type not in ['all', 'pos']:
            raise ValidationError(_('Cleanup type must be "All Types" or "POS Only" to use POS tax corrections.'))
    
    def _validate_tax_assignment_config(self):
        """Validate tax assignment configuration before opening wizard"""
        self.ensure_one()
        # Check if product module is available
        try:
            if not self.env.get('product.category'):
                raise ValidationError(_('The Product module is not installed or not available. Please ensure the product module is installed.'))
        except Exception:
            raise ValidationError(_('The Product module is not installed or not available. Please ensure the product module is installed.'))
    
    def _get_pos_domain(self):
        """Get domain for POS orders based on configuration"""
        # Check if POS is available
        if not self._is_pos_available():
            return None
        
        domain = []
        
        # Filter by cleanup type
        if self.cleanup_type not in ['all', 'pos']:
            return None
        
        if not self.cleanup_pos_taxes:
            return None
        
        # Filter by state
        domain.append(('state', 'in', ['done', 'paid']))
        
        # Filter by date range
        if self.pos_date_from:
            domain.append(('date_order', '>=', self.pos_date_from))
        if self.pos_date_to:
            domain.append(('date_order', '<=', self.pos_date_to))
        
        return domain
    
    def _detect_pos_tax_issues(self, pos_order_ids=None):
        """Detect POS tax issues based on configuration"""
        # Check if POS is available
        if not self._is_pos_available():
            return []
        
        LogLine = self.env['cleanup.log.line']
        
        if not pos_order_ids:
            pos_domain = self._get_pos_domain()
            if not pos_domain:
                return []
            pos_orders = self.env['pos.order'].search(pos_domain)
            pos_order_ids = pos_orders.ids
        
        if not pos_order_ids:
            return []
        
        # Query para detectar problemas de impuestos
        query = """
        SELECT 
            pol.id as line_id,
            pol.product_id,
            pol.order_id,
            pol.price_subtotal,
            pol.price_subtotal_incl,
            pol.qty,
            pt.id as template_id,
            COALESCE(array_agg(DISTINCT ptr.tax_id) FILTER (WHERE ptr.tax_id IS NOT NULL), ARRAY[]::integer[]) as expected_tax_ids,
            COALESCE(array_agg(DISTINCT atpol.account_tax_id) FILTER (WHERE atpol.account_tax_id IS NOT NULL), ARRAY[]::integer[]) as applied_tax_ids
        FROM pos_order_line pol
        JOIN product_product pp ON pol.product_id = pp.id
        JOIN product_template pt ON pp.product_tmpl_id = pt.id
        LEFT JOIN product_taxes_rel ptr ON pt.id = ptr.prod_id
        LEFT JOIN account_tax at_expected ON ptr.tax_id = at_expected.id AND at_expected.type_tax_use = 'sale'
        LEFT JOIN account_tax_pos_order_line_rel atpol ON pol.id = atpol.pos_order_line_id
        LEFT JOIN account_tax at_applied ON atpol.account_tax_id = at_applied.id
        WHERE pol.order_id IN %s
        GROUP BY pol.id, pol.product_id, pol.order_id, pol.price_subtotal, 
                 pol.price_subtotal_incl, pol.qty, pt.id
        """
        
        self.env.cr.execute(query, (tuple(pos_order_ids),))
        results = self.env.cr.dictfetchall()
        
        issues = []
        for result in results:
            # Clean tax IDs - remove None values and ensure we have lists of integers
            expected_raw = result.get('expected_tax_ids') or []
            applied_raw = result.get('applied_tax_ids') or []
            
            expected_tax_ids = [int(tid) for tid in expected_raw if tid is not None]
            applied_tax_ids = [int(tid) for tid in applied_raw if tid is not None]
            
            # Store cleaned lists back in result
            result['expected_tax_ids'] = expected_tax_ids
            result['applied_tax_ids'] = applied_tax_ids
            
            # Determine discrepancy type
            discrepancy_type = None
            if not applied_tax_ids and expected_tax_ids:
                discrepancy_type = 'missing'
            elif applied_tax_ids and not expected_tax_ids:
                discrepancy_type = 'extra'
            elif set(applied_tax_ids) != set(expected_tax_ids):
                discrepancy_type = 'incorrect'
            
            if discrepancy_type:
                # Filter based on correction type configuration
                include = False
                if self.pos_tax_correction_type == 'missing' and discrepancy_type == 'missing':
                    include = True
                elif self.pos_tax_correction_type == 'incorrect' and discrepancy_type == 'incorrect':
                    include = True
                elif self.pos_tax_correction_type == 'both' and discrepancy_type in ['missing', 'incorrect']:
                    include = True
                elif self.pos_tax_correction_type == 'all':
                    include = True
                
                if include:
                    result['discrepancy_type'] = discrepancy_type
                    issues.append(result)
        
        _logger.info("Detected %s POS tax issues", len(issues))
        
        return issues
    
    def _correct_pos_tax_issue(self, log_id, issue, log_line_model):
        """Correct a single POS tax issue"""
        line = self.env['pos.order.line'].browse(issue['line_id'])
        product = self.env['product.product'].browse(issue['product_id'])
        
        # Get expected taxes
        expected_tax_ids = list(filter(None, issue['expected_tax_ids'] or []))
        
        # If no expected taxes and default tax is configured, use it
        if not expected_tax_ids and self.pos_default_tax_id:
            expected_tax_ids = [self.pos_default_tax_id.id]
        
        # Calculate new values
        old_tax_ids = list(filter(None, issue['applied_tax_ids'] or []))
        new_tax_ids = expected_tax_ids
        
        # Update taxes
        old_vals = {'tax_ids': old_tax_ids}
        new_vals = {'tax_ids': new_tax_ids}
        
        # Apply changes (convert to Odoo write format)
        line.write({'tax_ids': [(6, 0, new_tax_ids)]})
        
        # Recalculate prices
        if new_tax_ids:
            taxes = self.env['account.tax'].browse(new_tax_ids)
            price_unit = line.price_unit or (line.price_subtotal / line.qty if line.qty else 0)
            tax_amount = sum(taxes.compute_all(price_unit, line.currency_id, line.qty)['taxes']) or 0
            new_total = line.price_subtotal + tax_amount
        else:
            new_total = line.price_subtotal
        
        # Create log line
        log_line_vals = {
            'log_id': log_id,
            'model_name': 'pos.order.line',
            'model_description': 'POS Order Line',
            'record_id': line.id,
            'record_name': line.display_name,
            'action_type': 'tax_correction',
            'old_values': json.dumps(old_vals),
            'new_values': json.dumps(new_vals),
            'product_id': product.id,
            'pos_order_line_id': line.id,
            'pos_order_id': line.order_id.id,
            'discrepancy_type': issue.get('discrepancy_type'),
            'price_subtotal_before': line.price_subtotal,
            'price_subtotal_after': line.price_subtotal,  # Same for subtotal
            'price_total_before': line.price_subtotal_incl,
            'price_total_after': new_total,
            'tax_amount_before': line.price_subtotal_incl - line.price_subtotal,
            'tax_amount_after': new_total - line.price_subtotal,
            'status': 'applied',
        }
        
        # Add tax relations
        expected_taxes = self.env['account.tax'].browse(expected_tax_ids)
        applied_taxes = self.env['account.tax'].browse(old_tax_ids)
        
        log_line = log_line_model.create(log_line_vals)
        log_line.expected_tax_ids = expected_taxes
        log_line.applied_tax_ids = applied_taxes
        
        # Update line total
        line.write({'price_subtotal_incl': new_total})
        
        return True
    
    def execute_cleanup(self):
        """Execute cleanup with logging and audit support"""
        self.ensure_one()
        
        # Create log if enabled
        log = None
        if self.enable_logging:
            log = self._create_cleanup_log()
        
        stock_count = 0
        purchase_count = 0
        account_count = 0
        pos_issues_count = 0
        pos_corrected_count = 0
        
        try:
            # Stock Moves cleanup (existing logic with logging)
            if self.cleanup_stock_moves and self.cleanup_type in ['all', 'stock']:
                stock_domain = []
                if self.stock_move_states != 'all':
                    if self.stock_move_states == 'cancel':
                        stock_domain.append(('state', '=', 'cancel'))
                    elif self.stock_move_states == 'blocked':
                        stock_domain.append(('state', '=', 'done'))
                    elif self.stock_move_states == 'both':
                        stock_domain.append(('state', 'in', ['done', 'cancel']))
                if self.date_from:
                    stock_domain.append(('create_date', '>=', self.date_from))
                if self.date_to:
                    stock_domain.append(('create_date', '<=', self.date_to))
                
                stock_moves = self.env['stock.move'].search(stock_domain)
                stock_count = len(stock_moves)
                
                for move in stock_moves:
                    old_state = move.state
                    if self.action_type == 'cancel':
                        move.write({'state': 'cancel'})
                        # Log here if enabled
                        if log:
                            self._log_record_change(
                                log.id,
                                move,
                                'state_change',
                                {'state': old_state},
                                {'state': 'cancel'}
                            )
                    elif self.action_type == 'delete':
                        # Log before delete if enabled
                        if log:
                            # Store all fields for potential restore
                            fields_to_store = ['state', 'product_id', 'location_id', 'location_dest_id', 'product_uom_qty', 'name', 'reference', 'create_date', 'create_uid']
                            old_vals = {f: getattr(move, f) for f in fields_to_store if hasattr(move, f)}
                            self._log_record_change(
                                log.id,
                                move,
                                'delete',
                                old_vals,
                                {}
                            )
                        move.unlink()
                    elif self.action_type == 'cancel_delete':
                        move.write({'state': 'cancel'})
                        # Log before delete if enabled
                        if log:
                            # Store all fields for potential restore
                            fields_to_store = ['state', 'product_id', 'location_id', 'location_dest_id', 'product_uom_qty', 'name', 'reference', 'create_date', 'create_uid']
                            old_vals = {f: getattr(move, f) for f in fields_to_store if hasattr(move, f)}
                            self._log_record_change(
                                log.id,
                                move,
                                'delete',
                                old_vals,
                                {}
                            )
                        move.unlink()
            
            # Purchase Orders cleanup (similar pattern)
            if self.cleanup_purchase_orders and self.cleanup_type in ['all', 'purchase']:
                purchase_domain = []
                if self.purchase_order_states != 'all':
                    if self.purchase_order_states == 'cancel':
                        purchase_domain.append(('state', '=', 'cancel'))
                    elif self.purchase_order_states == 'blocked':
                        purchase_domain.append(('state', '=', 'done'))
                    elif self.purchase_order_states == 'both':
                        purchase_domain.append(('state', 'in', ['done', 'cancel']))
                if self.date_from:
                    purchase_domain.append(('create_date', '>=', self.date_from))
                if self.date_to:
                    purchase_domain.append(('create_date', '<=', self.date_to))
                
                purchase_orders = self.env['purchase.order'].search(purchase_domain)
                purchase_count = len(purchase_orders)
                
                for order in purchase_orders:
                    old_state = order.state
                    if self.action_type == 'cancel':
                        order.write({'state': 'cancel'})
                        if log:
                            self._log_record_change(
                                log.id,
                                order,
                                'state_change',
                                {'state': old_state},
                                {'state': 'cancel'}
                            )
                    elif self.action_type == 'delete':
                        if log:
                            fields_to_store = ['state', 'partner_id', 'date_order', 'name', 'amount_total', 'create_date', 'create_uid']
                            old_vals = {f: getattr(order, f) for f in fields_to_store if hasattr(order, f)}
                            self._log_record_change(
                                log.id,
                                order,
                                'delete',
                                old_vals,
                                {}
                            )
                        order.unlink()
                    elif self.action_type == 'cancel_delete':
                        order.write({'state': 'cancel'})
                        if log:
                            fields_to_store = ['state', 'partner_id', 'date_order', 'name', 'amount_total', 'create_date', 'create_uid']
                            old_vals = {f: getattr(order, f) for f in fields_to_store if hasattr(order, f)}
                            self._log_record_change(
                                log.id,
                                order,
                                'delete',
                                old_vals,
                                {}
                            )
                        order.unlink()
            
            # Account Moves cleanup (similar pattern)
            if self.cleanup_account_moves and self.cleanup_type in ['all', 'account']:
                account_domain = []
                if self.account_move_states != 'all':
                    if self.account_move_states == 'cancel':
                        account_domain.append(('state', '=', 'cancel'))
                    elif self.account_move_states == 'blocked':
                        account_domain.append(('state', '=', 'posted'))
                    elif self.account_move_states == 'both':
                        account_domain.append(('state', 'in', ['posted', 'cancel']))
                if self.date_from:
                    account_domain.append(('create_date', '>=', self.date_from))
                if self.date_to:
                    account_domain.append(('create_date', '<=', self.date_to))
                
                account_moves = self.env['account.move'].search(account_domain)
                account_count = len(account_moves)
                
                for move in account_moves:
                    old_state = move.state
                    if self.action_type == 'cancel':
                        move.write({'state': 'cancel'})
                        if log:
                            self._log_record_change(
                                log.id,
                                move,
                                'state_change',
                                {'state': old_state},
                                {'state': 'cancel'}
                            )
                    elif self.action_type == 'delete':
                        if log:
                            fields_to_store = ['state', 'partner_id', 'date', 'name', 'amount_total', 'journal_id', 'create_date', 'create_uid']
                            old_vals = {f: getattr(move, f) for f in fields_to_store if hasattr(move, f)}
                            self._log_record_change(
                                log.id,
                                move,
                                'delete',
                                old_vals,
                                {}
                            )
                        move.unlink()
                    elif self.action_type == 'cancel_delete':
                        move.write({'state': 'cancel'})
                        if log:
                            fields_to_store = ['state', 'partner_id', 'date', 'name', 'amount_total', 'journal_id', 'create_date', 'create_uid']
                            old_vals = {f: getattr(move, f) for f in fields_to_store if hasattr(move, f)}
                            self._log_record_change(
                                log.id,
                                move,
                                'delete',
                                old_vals,
                                {}
                            )
                        move.unlink()
            
            # POS Tax correction
            if self.cleanup_pos_taxes and self.cleanup_type in ['all', 'pos']:
                if self.pos_tax_action in ['correct', 'cancel']:
                    # Get POS orders based on configuration
                    pos_domain = self._get_pos_domain()
                    if pos_domain:
                        pos_orders = self.env['pos.order'].search(pos_domain)
                        pos_order_ids = pos_orders.ids
                        
                        # Detect issues
                        issues = self._detect_pos_tax_issues(pos_order_ids)
                        pos_issues_count = len(issues)
                        
                        if self.pos_tax_action == 'correct':
                            LogLine = self.env['cleanup.log.line']
                            for issue in issues:
                                try:
                                    corrected = self._correct_pos_tax_issue(log.id if log else False, issue, LogLine)
                                    if corrected:
                                        pos_corrected_count += 1
                                except Exception as e:
                                    if log:
                                        log._add_error(f"Failed to correct POS line {issue['line_id']}: {str(e)}")
                        elif self.pos_tax_action == 'cancel':
                            # Cancel orders with tax issues
                            orders_to_cancel = self.env['pos.order'].browse(
                                list(set([issue['order_id'] for issue in issues]))
                            )
                            for order in orders_to_cancel:
                                order.write({'state': 'cancel'})
            
            # Update results
            update_vals = {
                'last_execution': fields.Datetime.now(),
                'stock_moves_processed': stock_count,
                'purchase_orders_processed': purchase_count,
                'account_moves_processed': account_count,
                'pos_orders_processed': pos_issues_count,
                'pos_lines_processed': pos_issues_count,
                'pos_lines_corrected': pos_corrected_count,
            }
            
            if log:
                update_vals['last_log_id'] = log.id
                log.write({
                    'status': 'completed',
                    'total_processed': stock_count + purchase_count + account_count + pos_issues_count,
                    'total_corrected': pos_corrected_count,
                    'stock_moves_processed': stock_count,
                    'purchase_orders_processed': purchase_count,
                    'account_moves_processed': account_count,
                    'pos_orders_processed': pos_issues_count,
                    'pos_lines_processed': pos_issues_count,
                    'pos_lines_corrected': pos_corrected_count,
                })
            
            self.write(update_vals)
            
            # Return success notification
            message_parts = []
            if stock_count > 0:
                message_parts.append(_('%s stock moves') % stock_count)
            if purchase_count > 0:
                message_parts.append(_('%s purchase orders') % purchase_count)
            if account_count > 0:
                message_parts.append(_('%s account moves') % account_count)
            if pos_issues_count > 0:
                message_parts.append(_('%s POS tax issues (%s corrected)') % (pos_issues_count, pos_corrected_count))
            
            message = _('Processed: %s') % ', '.join(message_parts) if message_parts else _('No records processed')
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cleanup Completed'),
                    'message': message,
                    'sticky': False,
                }
            }
            
        except Exception as e:
            # Update log with error
            if log:
                log.write({
                    'status': 'failed',
                    'error_log': str(e),
                })
            
            raise
    
    def action_open_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Execute Cleanup'),
            'res_model': 'cleanup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_config_id': self.id},
        }
    
    def action_open_pos_tax_wizard(self):
        """Open POS tax correction wizard with validation interface"""
        self.ensure_one()
        # Validate configuration before opening wizard
        self._validate_pos_config()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Validate POS Tax Corrections'),
            'res_model': 'cleanup.pos.tax.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_config_id': self.id,
                'default_pos_tax_action': self.pos_tax_action,
            },
        }
    
    def action_open_tax_assignment_wizard(self):
        """Open tax assignment by category wizard"""
        self.ensure_one()
        # Validate configuration before opening wizard
        self._validate_tax_assignment_config()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assign Taxes by Category'),
            'res_model': 'cleanup.tax.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_config_id': self.id,
            },
        }
    
    @api.model
    def _cron_execute_cleanup(self):
        """Method called by cron job to execute cleanup for all active configurations"""
        active_configs = self.search([('active', '=', True)])
        for config in active_configs:
            try:
                config.execute_cleanup()
            except Exception as e:
                # Log error but continue with other configs
                _logger.error("Failed to execute cleanup for config %s: %s", config.name, str(e))