# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP & Developer.
# © 2026.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class POSBomSimulation(models.Model):
    _name = 'pos.bom.simulation'
    _description = 'POS & MRP BoM Simulation'
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New Simulation')
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('done', 'Completed'),
        ('failed', 'Failed')
    ], string='Status', default='draft', readonly=True)

    raw_material_qty_init = fields.Float(
        string='Initial Material Stock',
        default=100.0,
        required=True,
        help="Initial stock level to assign to raw materials before the sale."
    )
    sale_qty = fields.Float(
        string='Sale Quantity (Pizza)',
        default=2.0,
        required=True,
        help="Quantity of Pizza ordered in POS and manufactured in MRP."
    )
    adjust_component_stock = fields.Boolean(
        string='Adjust Ingredient Stock?',
        default=True,
        help="If checked, the simulation will add initial stock to the BOM components."
    )
    error_message = fields.Text(string='Error Details', readonly=True)

    # Selected/Generated Finished Product
    finished_product_id = fields.Many2one(
        'product.product',
        string='Finished Product',
        domain="['|', ('is_pos_bom', '=', True), ('available_in_pos', '=', True)]",
        help="Select an existing product with BoM config, or leave empty to auto-generate a mock Pizza."
    )

    # Generated/Associated Records
    raw_material_1_id = fields.Many2one('product.product', string='Dough Product (Component 1)', readonly=True)
    raw_material_2_id = fields.Many2one('product.product', string='Tomato Sauce Product (Component 2)', readonly=True)
    raw_material_ids = fields.Many2many('product.product', string='All Components Used', readonly=True)

    pos_bom_id = fields.Many2one('pos.product.bom', string='POS BoM Structure', readonly=True)
    mrp_bom_id = fields.Many2one('mrp.bom', string='MRP BoM Structure', readonly=True)

    mrp_production_id = fields.Many2one('mrp.production', string='Manufacturing Order', readonly=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Order', readonly=True)
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', readonly=True)
    account_move_ids = fields.Many2many('account.move', string='Accounting Entries', readonly=True)

    # Results
    rm1_final_qty = fields.Float(string='Final Dough Stock', readonly=True)
    rm2_final_qty = fields.Float(string='Final Sauce Stock', readonly=True)

    pos_config_id = fields.Many2one('pos.config', string='POS Config Used', readonly=True)
    pos_session_id = fields.Many2one('pos.session', string='POS Session Used', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New Simulation')) == _('New Simulation'):
                seq = self.env['ir.sequence'].next_by_code('pos.bom.simulation') or '/'
                if seq == '/':
                    last_sim = self.search([], limit=1, order='id desc')
                    last_id = last_sim.id if last_sim else 0
                    seq = f"SIM/{fields.Date.today().year}/{last_id + 1:04d}"
                vals['name'] = seq
        return super(POSBomSimulation, self).create(vals_list)

    def action_run_simulation(self):
        self.ensure_one()
        self.state = 'running'
        self.error_message = False

        # Use savepoint to handle transactional errors
        self.env.cr.execute('SAVEPOINT simulation_run_sp')
        try:
            suffix = f" (Sim #{self.id})"
            categ = self.env.ref('product.product_category_all')

            # 1. Determine or Create Finished Product & BoM Structures
            if self.finished_product_id:
                finished_product = self.finished_product_id
                
                # Check for existing BoMs
                pos_bom = self.env['pos.product.bom'].search([('product_id', '=', finished_product.id)], limit=1)
                mrp_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', finished_product.product_tmpl_id.id)], limit=1)
                
                if not pos_bom and not mrp_bom:
                    raise UserError(_("The selected product '%s' does not have a POS BOM or an MRP BOM.") % finished_product.name)

                # Ensure is_pos_bom and available_in_pos are True
                finished_product.write({
                    'is_pos_bom': True,
                    'available_in_pos': True,
                    'sale_ok': True,
                })

                # Collect components
                components = self.env['product.product']
                if pos_bom:
                    components |= pos_bom.product_bom_line_ids.mapped('product_id')
                if mrp_bom:
                    components |= mrp_bom.bom_line_ids.mapped('product_id')

                if not components:
                    raise UserError(_("No components found in the BOMs of product '%s'.") % finished_product.name)

                raw_material_1 = components[0] if len(components) > 0 else False
                raw_material_2 = components[1] if len(components) > 1 else False

            else:
                # Fallback to automatic dynamic product creation
                finished_product = self.env['product.product'].create({
                    'name': 'Simulation Pizza' + suffix,
                    'is_storable': True,
                    'available_in_pos': True,
                    'sale_ok': True,
                    'lst_price': 40.0,
                    'standard_price': 20.0,
                    'categ_id': categ.id,
                    'is_pos_bom': True,
                })

                raw_material_1 = self.env['product.product'].create({
                    'name': 'Simulation Dough' + suffix,
                    'is_storable': True,
                    'available_in_pos': False,
                    'sale_ok': False,
                    'lst_price': 10.0,
                    'standard_price': 5.0,
                    'categ_id': categ.id,
                })

                raw_material_2 = self.env['product.product'].create({
                    'name': 'Simulation Tomato Sauce' + suffix,
                    'is_storable': True,
                    'available_in_pos': False,
                    'sale_ok': False,
                    'lst_price': 15.0,
                    'standard_price': 7.5,
                    'categ_id': categ.id,
                })

                components = raw_material_1 | raw_material_2

                # Create POS BoM
                pos_bom = self.env['pos.product.bom'].create({
                    'product_id': finished_product.id,
                    'product_qty': 1.0,
                    'product_uom_id': finished_product.uom_id.id,
                })
                self.env['pos.product.bom.line'].create({
                    'pos_bom_id': pos_bom.id,
                    'product_id': raw_material_1.id,
                    'product_qty': 2.0,
                    'product_uom_id': raw_material_1.uom_id.id,
                })
                self.env['pos.product.bom.line'].create({
                    'pos_bom_id': pos_bom.id,
                    'product_id': raw_material_2.id,
                    'product_qty': 3.0,
                    'product_uom_id': raw_material_2.uom_id.id,
                })
                pos_bom.confirm_bom()

                # Create MRP BoM
                mrp_bom = self.env['mrp.bom'].create({
                    'product_tmpl_id': finished_product.product_tmpl_id.id,
                    'product_qty': 1.0,
                    'product_uom_id': finished_product.uom_id.id,
                    'type': 'normal',
                })
                self.env['mrp.bom.line'].create({
                    'bom_id': mrp_bom.id,
                    'product_id': raw_material_1.id,
                    'product_qty': 2.0,
                    'product_uom_id': raw_material_1.uom_id.id,
                })
                self.env['mrp.bom.line'].create({
                    'bom_id': mrp_bom.id,
                    'product_id': raw_material_2.id,
                    'product_qty': 3.0,
                    'product_uom_id': raw_material_2.uom_id.id,
                })

            # 2. Add Stock Level to Components (Ingredients)
            if self.adjust_component_stock:
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
                if not warehouse:
                    raise UserError(_("No warehouse found for company %s.") % self.env.company.name)
                location = warehouse.lot_stock_id

                for rm in components:
                    self.env['stock.quant'].with_context(inventory_mode=True).create({
                        'product_id': rm.id,
                        'inventory_quantity': self.raw_material_qty_init,
                        'location_id': location.id,
                    }).action_apply_inventory()

            # 3. Execute Manufacturing Order (MRP Production) if MRP BOM exists
            mrp_production = False
            if mrp_bom:
                mrp_production = self.env['mrp.production'].create({
                    'product_id': finished_product.id,
                    'bom_id': mrp_bom.id,
                    'product_qty': self.sale_qty,
                    'product_uom_id': finished_product.uom_id.id,
                })
                mrp_production.action_confirm()
                mrp_production.action_assign()
                
                mrp_production.write({'qty_producing': self.sale_qty})
                for move in mrp_production.move_raw_ids:
                    move.write({
                        'picked': True,
                        'quantity': move.product_uom_qty,
                    })
                mrp_production.button_mark_done()

            # 4. Setup POS Environment
            pos_config = self.env['pos.config'].search([('name', '=', 'Simulation POS')], limit=1)
            if not pos_config:
                journal = self.env['account.journal'].search([
                    ('type', '=', 'sale'),
                    ('company_id', '=', self.env.company.id)
                ], limit=1)
                pos_config = self.env['pos.config'].create({
                    'name': 'Simulation POS',
                    'journal_id': journal.id,
                })

            payment_method = pos_config.payment_method_ids[:1]
            if not payment_method:
                payment_method = self.env['pos.payment.method'].search([('company_id', '=', self.env.company.id)], limit=1)
                if not payment_method:
                    receivable_acc = self.env['account.account'].search([
                        ('account_type', '=', 'asset_receivable'),
                        ('company_ids', '=', self.env.company.id)
                    ], limit=1)
                    journal_cash = self.env['account.journal'].search([
                        ('type', '=', 'cash'),
                        ('company_id', '=', self.env.company.id)
                    ], limit=1)
                    payment_method = self.env['pos.payment.method'].create({
                        'name': 'Simulation Cash',
                        'receivable_account_id': receivable_acc.id,
                        'journal_id': journal_cash.id,
                        'company_id': self.env.company.id,
                    })
                pos_config.write({'payment_method_ids': [(4, payment_method.id)]})

            if not pos_config.current_session_id:
                pos_session = self.env['pos.session'].create({
                    'config_id': pos_config.id,
                    'user_id': self.env.user.id,
                })
                pos_session.action_pos_session_open()
            else:
                pos_session = pos_config.current_session_id

            # 5. Create POS Order
            partner = self.env['res.partner'].search([('name', '=', 'Simulation Customer')], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': 'Simulation Customer',
                })

            amount_total = finished_product.lst_price * self.sale_qty
            pos_order = self.env['pos.order'].create({
                'session_id': pos_session.id,
                'partner_id': partner.id,
                'amount_tax': 0.0,
                'amount_total': amount_total,
                'amount_paid': 0.0,
                'amount_return': 0.0,
                'lines': [(0, 0, {
                    'product_id': finished_product.id,
                    'qty': self.sale_qty,
                    'price_unit': finished_product.lst_price,
                    'price_subtotal': amount_total,
                    'price_subtotal_incl': amount_total,
                })],
            })

            pos_order.add_payment({
                'amount': amount_total,
                'payment_date': fields.Datetime.now(),
                'payment_method_id': payment_method.id,
            })
            pos_order.action_pos_order_paid()

            # Create Picking
            pos_order._create_order_picking()
            picking = pos_order.picking_ids[:1]

            # 6. Close Session
            cash_payment_method = pos_session.payment_method_ids.filtered(lambda pm: pm.is_cash_count)[:1]
            if cash_payment_method:
                total_cash_payment = sum(pos_session.mapped('order_ids.payment_ids').filtered(
                    lambda payment: payment.payment_method_id.id == cash_payment_method.id
                ).mapped('amount'))
                try:
                    pos_session.post_closing_cash_details(total_cash_payment)
                except Exception:
                    pass

            pos_session.close_session_from_ui()

            # Find generated account moves
            account_moves = self.env['account.move'].search([
                '|',
                ('ref', 'ilike', pos_session.name),
                ('ref', 'ilike', pos_order.name)
            ])

            # Get final stocks
            rm1_final = raw_material_1.qty_available if raw_material_1 else 0.0
            rm2_final = raw_material_2.qty_available if raw_material_2 else 0.0

            # Update simulation record
            self.write({
                'state': 'done',
                'finished_product_id': finished_product.id,
                'raw_material_1_id': raw_material_1.id if raw_material_1 else False,
                'raw_material_2_id': raw_material_2.id if raw_material_2 else False,
                'raw_material_ids': [(6, 0, components.ids)],
                'pos_bom_id': pos_bom.id if pos_bom else False,
                'mrp_bom_id': mrp_bom.id if mrp_bom else False,
                'mrp_production_id': mrp_production.id if mrp_production else False,
                'pos_order_id': pos_order.id,
                'stock_picking_id': picking.id if picking else False,
                'account_move_ids': [(6, 0, account_moves.ids)],
                'rm1_final_qty': rm1_final,
                'rm2_final_qty': rm2_final,
                'pos_config_id': pos_config.id,
                'pos_session_id': pos_session.id,
            })
            self.env.cr.execute('RELEASE SAVEPOINT simulation_run_sp')

        except Exception as e:
            self.env.cr.execute('ROLLBACK TO SAVEPOINT simulation_run_sp')
            self.write({
                'state': 'failed',
                'error_message': str(e),
            })
            raise UserError(_("Error executing simulation: %s") % str(e))

        return True

    # Smart Button Actions
    def action_view_products(self):
        self.ensure_one()
        product_ids = [self.finished_product_id.id] + self.raw_material_ids.ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Simulation Products',
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'domain': [('id', 'in', product_ids)],
            'target': 'current',
        }

    def action_view_pos_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'POS Order',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': self.pos_order_id.id,
            'target': 'current',
        }

    def action_view_mrp_production(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Manufacturing Order',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.mrp_production_id.id,
            'target': 'current',
        }

    def action_view_stock_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Picking',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.stock_picking_id.id,
            'target': 'current',
        }

    def action_view_account_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Accounting Entries',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.account_move_ids.ids)],
            'target': 'current',
        }
