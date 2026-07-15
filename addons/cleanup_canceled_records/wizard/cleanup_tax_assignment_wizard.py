# -*- coding: utf-8 -*-
import logging, traceback
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json

_logger = logging.getLogger(__name__)


class CleanupTaxAssignmentWizard(models.TransientModel):
    _name = 'cleanup.tax.assignment.wizard'
    _description = 'Tax Assignment by Category Wizard'
    
    config_id = fields.Many2one('cleanup.config', string='Configuration', required=True)
    
    # Configuration fields
    category_ids = fields.Many2many('product.category',
        relation='cleanup_tax_assignment_category_rel',
        column1='wizard_id',
        column2='category_id',
        string='Product Categories', required=True)
    sale_tax_ids = fields.Many2many('account.tax',
        relation='cleanup_tax_assignment_sale_tax_rel',
        column1='wizard_id',
        column2='tax_id',
        string='Sale Taxes',
        domain=[('type_tax_use', '=', 'sale')])
    purchase_tax_ids = fields.Many2many('account.tax',
        relation='cleanup_tax_assignment_purchase_tax_rel',
        column1='wizard_id',
        column2='tax_id',
        string='Purchase Taxes',
        domain=[('type_tax_use', '=', 'purchase')])
    
    # Options
    apply_to_all_products = fields.Boolean(string='Apply to All Products in Category', default=True)
    override_existing_taxes = fields.Boolean(string='Override Existing Taxes', default=True,
        help='If unchecked, only set taxes where currently empty')
    also_update_variants = fields.Boolean(string='Also Update Variants', default=True,
        help='Update taxes on product variants (product.product) as well')
    
    # Progress
    state = fields.Selection([
        ('config', 'Configuration'),
        ('detection', 'Detection'),
        ('validation', 'Validation'),
        ('execution', 'Execution'),
        ('results', 'Results'),
    ], string='State', default='config')
    
    # Detection results
    total_products_detected = fields.Integer(string='Total Products Detected', readonly=True)
    products_with_sale_taxes = fields.Integer(string='Products with Sale Taxes', readonly=True)
    products_with_purchase_taxes = fields.Integer(string='Products with Purchase Taxes', readonly=True)
    
    # Validation lines
    validation_line_ids = fields.One2many('cleanup.tax.assignment.line', 'wizard_id', string='Validation Lines')
    
    # Execution results
    products_processed = fields.Integer(string='Products Processed', readonly=True)
    products_updated = fields.Integer(string='Products Updated', readonly=True)
    products_failed = fields.Integer(string='Products Failed', readonly=True)
    error_log = fields.Text(string='Error Log', readonly=True)
    
    # Log reference
    log_id = fields.Many2one('cleanup.log', string='Log Reference', readonly=True)
    
    # Methods
    def _check_models_available(self):
        """Check if required models are available"""
        required_models = ['product.category', 'product.template', 'account.tax']
        for model_name in required_models:
            if not self.env.get(model_name):
                _logger.error("Required model %s is not available", model_name)
                return False
        return True
    
    @api.model
    def default_get(self, fields_list):
        """Set default values from context"""
        try:
            res = super(CleanupTaxAssignmentWizard, self).default_get(fields_list)
            # Set config_id from context if not already set
            if 'config_id' not in res and self.env.context.get('default_config_id'):
                res['config_id'] = self.env.context.get('default_config_id')
            return res
        except Exception as e:
            _logger.error("Error in default_get: %s\n%s", e, traceback.format_exc())
            raise
    
    @api.onchange('config_id')
    def _onchange_config_id(self):
        """Load default values from config if any"""
        # No specific config fields for tax assignment yet
        pass
    
    def action_detect_products(self):
        """Detect products based on selected categories and compute tax changes"""
        self.ensure_one()
        
        _logger.info("Starting tax assignment detection for wizard %s", self.id)
        
        # Check if required models are available
        if not self._check_models_available():
            _logger.error("Required models not available for tax assignment")
            raise UserError(_('Required models are not available. Please ensure the product and account modules are installed.'))
        
        if not self.category_ids:
            _logger.warning("No product categories selected")
            raise UserError(_('Please select at least one product category'))
        
        _logger.info("Selected categories: %s", self.category_ids.ids)
        
        # Clear existing validation lines
        self.validation_line_ids.unlink()
        
        # Build domain for products
        domain = [('categ_id', 'in', self.category_ids.ids)]
        if not self.apply_to_all_products:
            # Only products without taxes? Not implemented yet
            pass
        
        _logger.info("Searching products with domain: %s", domain)
        products = self.env['product.template'].search(domain)
        _logger.info("Found %s products in selected categories", len(products))
        
        # Create validation lines
        ValidationLine = self.env['cleanup.tax.assignment.line']
        validation_lines = []
        
        for product in products:
            line_vals = {
                'wizard_id': self.id,
                'product_tmpl_id': product.id,
                'product_category_id': product.categ_id.id,
                'current_sale_tax_ids': [(6, 0, product.taxes_id.ids)],
                'current_purchase_tax_ids': [(6, 0, product.supplier_taxes_id.ids)],
                'new_sale_tax_ids': [(6, 0, self.sale_tax_ids.ids)],
                'new_purchase_tax_ids': [(6, 0, self.purchase_tax_ids.ids)],
                'override_existing': self.override_existing_taxes,
            }
            validation_lines.append((0, 0, line_vals))
        
        # Update counts
        self.write({
            'state': 'validation',
            'total_products_detected': len(products),
            'products_with_sale_taxes': len(products.filtered(lambda p: p.taxes_id)),
            'products_with_purchase_taxes': len(products.filtered(lambda p: p.supplier_taxes_id)),
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
    
    def action_calculate_impact(self):
        """Calculate impact of tax changes (e.g., number of POS lines affected)"""
        self.ensure_one()
        # TODO: Implement impact calculation
        # Could query POS lines for these products to show how many need correction
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_execute_assignment(self):
        """Execute tax assignment for selected lines"""
        self.ensure_one()
        
        selected_lines = self.validation_line_ids.filtered(lambda l: l.selected)
        if not selected_lines:
            raise UserError(_('Please select at least one product to update'))
        
        # Create log if enabled
        log = None
        if self.config_id.enable_logging:
            log = self.config_id._create_cleanup_log()
            self.log_id = log.id
        
        products_processed = 0
        products_updated = 0
        products_failed = 0
        error_messages = []
        
        for line in selected_lines:
            try:
                product = line.product_tmpl_id
                
                # Determine new taxes based on override logic
                new_sale_taxes = line.new_sale_tax_ids.ids
                new_purchase_taxes = line.new_purchase_tax_ids.ids
                
                if not line.override_existing:
                    # Keep existing taxes if present, otherwise use new
                    if product.taxes_id:
                        new_sale_taxes = product.taxes_id.ids
                    if product.supplier_taxes_id:
                        new_purchase_taxes = product.supplier_taxes_id.ids
                
                # Prepare old values for logging
                old_vals = {
                    'taxes_id': product.taxes_id.ids,
                    'supplier_taxes_id': product.supplier_taxes_id.ids,
                }
                new_vals = {
                    'taxes_id': new_sale_taxes,
                    'supplier_taxes_id': new_purchase_taxes,
                }
                
                # Update product
                product.write({
                    'taxes_id': [(6, 0, new_sale_taxes)],
                    'supplier_taxes_id': [(6, 0, new_purchase_taxes)],
                })
                
                # Create log line
                if log:
                    LogLine = self.env['cleanup.log.line']
                    log_line = LogLine._create_log_line(
                        log_id=log.id,
                        model=self.env['product.template'],
                        record=product,
                        action_type='tax_assignment',
                        old_vals=old_vals,
                        new_vals=new_vals,
                        product_id=product.product_variant_id.id,
                    )
                
                products_updated += 1
                products_processed += 1
                line.write({'status': 'updated'})
                
            except Exception as e:
                products_failed += 1
                products_processed += 1
                error_messages.append(f"Product {line.product_tmpl_id.display_name}: {str(e)}")
                line.write({'status': 'failed', 'error_message': str(e)})
        
        # Update log if exists
        if log:
            log.write({
                'status': 'completed',
                'total_processed': products_processed,
                'total_corrected': products_updated,
                'error_log': '\n'.join(error_messages) if error_messages else False,
            })
        
        # Update wizard
        self.write({
            'state': 'results',
            'products_processed': products_processed,
            'products_updated': products_updated,
            'products_failed': products_failed,
            'error_log': '\n'.join(error_messages) if error_messages else '',
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
    
    def action_correct_pos_taxes(self):
        """Open POS tax correction wizard for the same configuration"""
        self.ensure_one()
        return self.config_id.action_open_pos_tax_wizard()
    
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
    
    def create(self, vals):
        try:
            return super(CleanupTaxAssignmentWizard, self).create(vals)
        except Exception as e:
            _logger.error("Error creating tax assignment wizard: %s\n%s", e, traceback.format_exc())
            raise
    
    def action_cancel(self):
        """Cancel the wizard"""
        return {'type': 'ir.actions.act_window_close'}


class CleanupTaxAssignmentLine(models.TransientModel):
    _name = 'cleanup.tax.assignment.line'
    _description = 'Tax Assignment Validation Line'
    _order = 'product_category_id, product_tmpl_id'
    
    wizard_id = fields.Many2one('cleanup.tax.assignment.wizard', string='Wizard', required=True, ondelete='cascade')
    
    # Product information
    product_tmpl_id = fields.Many2one('product.template', string='Product', required=True, readonly=True)
    product_category_id = fields.Many2one('product.category', string='Category', readonly=True)
    
    # Tax information
    current_sale_tax_ids = fields.Many2many('account.tax',
        relation='cleanup_tax_assignment_line_current_sale_rel',
        column1='line_id',
        column2='tax_id',
        string='Current Sale Taxes', readonly=True)
    current_purchase_tax_ids = fields.Many2many('account.tax',
        relation='cleanup_tax_assignment_line_current_purchase_rel',
        column1='line_id',
        column2='tax_id',
        string='Current Purchase Taxes', readonly=True)
    new_sale_tax_ids = fields.Many2many('account.tax',
        relation='cleanup_tax_assignment_line_new_sale_rel',
        column1='line_id',
        column2='tax_id',
        string='New Sale Taxes', readonly=True)
    new_purchase_tax_ids = fields.Many2many('account.tax',
        relation='cleanup_tax_assignment_line_new_purchase_rel',
        column1='line_id',
        column2='tax_id',
        string='New Purchase Taxes', readonly=True)
    
    # Options
    override_existing = fields.Boolean(string='Override Existing', default=True)
    
    # Action
    selected = fields.Boolean(string='Select', default=True)
    action = fields.Selection([
        ('update', 'Update Taxes'),
        ('keep', 'Keep Current'),
        ('custom', 'Custom'),
    ], string='Action', default='update')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('updated', 'Updated'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ], string='Status', default='pending', readonly=True)
    
    error_message = fields.Text(string='Error Message', readonly=True)
    
    # Methods
    def name_get(self):
        result = []
        for line in self:
            name = line.product_tmpl_id.display_name
            result.append((line.id, name))
        return result
    
    def action_view_product(self):
        """View the product template"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product'),
            'res_model': 'product.template',
            'res_id': self.product_tmpl_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_category(self):
        """View the product category"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product Category'),
            'res_model': 'product.category',
            'res_id': self.product_category_id.id,
            'view_mode': 'form',
            'target': 'current',
        }