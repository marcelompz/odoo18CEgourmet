# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CleanupWizard(models.TransientModel):
    _name = 'cleanup.wizard'
    _description = 'Cleanup Wizard'
    
    config_id = fields.Many2one('cleanup.config', string='Configuration', required=True)
    
    # Override options
    override_action = fields.Boolean(string='Override Action')
    action_type = fields.Selection([
        ('cancel', 'Only Cancel'),
        ('delete', 'Delete Permanently'),
        ('cancel_delete', 'Cancel then Delete'),
    ], string='Action Type')
    
    # Counts preview
    stock_moves_count = fields.Integer(string='Stock Moves to Process', readonly=True)
    purchase_orders_count = fields.Integer(string='Purchase Orders to Process', readonly=True)
    account_moves_count = fields.Integer(string='Account Moves to Process', readonly=True)
    
    @api.onchange('config_id')
    def _onchange_config_id(self):
        if self.config_id:
            # Calculate counts based on configuration
            stock_count = 0
            purchase_count = 0
            account_count = 0
            
            # Stock Moves
            if self.config_id.cleanup_stock_moves:
                stock_domain = []
                if self.config_id.stock_move_states != 'all':
                    if self.config_id.stock_move_states == 'cancel':
                        stock_domain.append(('state', '=', 'cancel'))
                    elif self.config_id.stock_move_states == 'blocked':
                        stock_domain.append(('state', '=', 'done'))
                    elif self.config_id.stock_move_states == 'both':
                        stock_domain.append(('state', 'in', ['done', 'cancel']))
                if self.config_id.date_from:
                    stock_domain.append(('create_date', '>=', self.config_id.date_from))
                if self.config_id.date_to:
                    stock_domain.append(('create_date', '<=', self.config_id.date_to))
                stock_count = self.env['stock.move'].search_count(stock_domain)
            
            # Purchase Orders
            if self.config_id.cleanup_purchase_orders:
                purchase_domain = []
                if self.config_id.purchase_order_states != 'all':
                    if self.config_id.purchase_order_states == 'cancel':
                        purchase_domain.append(('state', '=', 'cancel'))
                    elif self.config_id.purchase_order_states == 'blocked':
                        purchase_domain.append(('state', '=', 'done'))
                    elif self.config_id.purchase_order_states == 'both':
                        purchase_domain.append(('state', 'in', ['done', 'cancel']))
                if self.config_id.date_from:
                    purchase_domain.append(('create_date', '>=', self.config_id.date_from))
                if self.config_id.date_to:
                    purchase_domain.append(('create_date', '<=', self.config_id.date_to))
                purchase_count = self.env['purchase.order'].search_count(purchase_domain)
            
            # Account Moves
            if self.config_id.cleanup_account_moves:
                account_domain = []
                if self.config_id.account_move_states != 'all':
                    if self.config_id.account_move_states == 'cancel':
                        account_domain.append(('state', '=', 'cancel'))
                    elif self.config_id.account_move_states == 'blocked':
                        account_domain.append(('state', '=', 'posted'))
                    elif self.config_id.account_move_states == 'both':
                        account_domain.append(('state', 'in', ['posted', 'cancel']))
                if self.config_id.date_from:
                    account_domain.append(('create_date', '>=', self.config_id.date_from))
                if self.config_id.date_to:
                    account_domain.append(('create_date', '<=', self.config_id.date_to))
                account_count = self.env['account.move'].search_count(account_domain)
            
            self.stock_moves_count = stock_count
            self.purchase_orders_count = purchase_count
            self.account_moves_count = account_count
            
            # Set default action type from config
            self.action_type = self.config_id.action_type
    
    def action_execute(self):
        self.ensure_one()
        
        # Use overridden action type if specified
        action_type = self.action_type if self.override_action else self.config_id.action_type
        
        # Create a temporary copy of config with overridden action
        temp_config = self.config_id.copy({
            'action_type': action_type,
        })
        
        # Execute cleanup
        result = temp_config.execute_cleanup()
        
        # Delete temporary config
        temp_config.unlink()
        
        # Close wizard
        return result
    
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}