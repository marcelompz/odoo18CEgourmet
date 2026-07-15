# -*- coding: utf-8 -*-
import os
import json
import logging
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MigrationExportWizard(models.TransientModel):
    _name = 'migration.export.wizard'
    _description = 'Export Transactions'

    config_id = fields.Many2one('migration.config', string='Configuration', required=True)
    export_path = fields.Char(string='Export Path', related='config_id.export_path')
    result = fields.Text(string='Result', readonly=True)
    
    def action_export(self):
        self.ensure_one()
        cfg = self.config_id
        export_dir = cfg.export_path
        os.makedirs(export_dir, exist_ok=True)
        
        log_lines = []
        def log(msg):
            log_lines.append(msg)
            _logger.info(msg)
        
        try:
            # Authenticate
            session = requests.Session()
            r = session.post(f'{cfg.source_url}/web/session/authenticate', json={
                'jsonrpc': '2.0', 'method': 'call',
                'params': {
                    'db': cfg.source_db,
                    'login': cfg.source_user,
                    'password': cfg.source_password,
                }, 'id': 1
            })
            result = r.json()
            if 'error' in result:
                raise UserError(f"Auth error: {result['error']}")
            
            def exec_kw(model, method, args=None, kwargs=None):
                url = f"{cfg.source_url}/web/dataset/call_kw/{model}/{method}"
                return session.post(url, json={
                    'jsonrpc': '2.0', 'method': 'call',
                    'params': {'model': model, 'method': method, 'args': args or [], 'kwargs': kwargs or {}},
                    'id': 1
                }).json().get('result')
            
            # Export POS Orders
            log("📦 Exporting POS Orders...")
            pos_ids = exec_kw('pos.order', 'search', [[
                ('state', 'in', ['done', 'invoiced', 'paid']),
                ('date_order', '>=', str(cfg.start_date)),
                ('date_order', '<=', str(cfg.end_date)),
            ]], {'limit': 10000})
            
            if pos_ids:
                pos_orders = exec_kw('pos.order', 'read', [pos_ids, [
                    'id', 'name', 'partner_id', 'date_order', 'state', 'company_id',
                    'currency_id', 'pricelist_id', 'session_id', 'config_id',
                    'sequence_number', 'amount_total', 'amount_tax', 'amount_paid',
                    'payment_ids', 'pos_reference', 'fiscal_position_id',
                ]])
                
                pos_line_ids = exec_kw('pos.order.line', 'search', [[('order_id', 'in', pos_ids)]], {'limit': 50000})
                pos_lines = exec_kw('pos.order.line', 'read', [pos_line_ids, [
                    'id', 'order_id', 'product_id', 'name', 'qty', 'price_unit',
                    'price_subtotal', 'price_subtotal_incl', 'discount', 'full_product_name',
                    'company_id', 'notice', 'customer_note', 'price_extra',
                    'margin', 'margin_percent', 'total_cost',
                ]]) if pos_line_ids else []
                
                payment_ids = exec_kw('pos.payment', 'search', [[('pos_order_id', 'in', pos_ids)]], {'limit': 10000})
                payments = exec_kw('pos.payment', 'read', [payment_ids, [
                    'id', 'pos_order_id', 'payment_method_id', 'amount', 'payment_date',
                    'payment_currency_id', 'session_id', 'company_id',
                ]]) if payment_ids else []
                
                session_ids = list(set([o['session_id'][0] for o in pos_orders if o.get('session_id')]))
                sessions = exec_kw('pos.session', 'read', [session_ids, [
                    'id', 'name', 'config_id', 'user_id', 'start_at', 'stop_at', 'state', 'sequence_number',
                ]])
                
                for fn, data in [('pos_orders.json', pos_orders), ('pos_order_lines.json', pos_lines),
                                 ('pos_payments.json', payments), ('pos_sessions.json', sessions)]:
                    with open(os.path.join(export_dir, fn), 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                
                log(f"✅ POS: {len(pos_orders)} orders, {len(pos_lines)} lines, {len(payments)} payments")
            
            # Export Purchase Orders
            log("📦 Exporting Purchase Orders...")
            po_ids = exec_kw('purchase.order', 'search', [[
                ('state', 'in', ['purchase', 'done']),
                ('date_approve', '>=', str(cfg.start_date)),
                ('date_approve', '<=', str(cfg.end_date)),
            ]], {'limit': 10000})
            
            if po_ids:
                purchases = exec_kw('purchase.order', 'read', [po_ids, [
                    'id', 'name', 'partner_id', 'date_order', 'date_approve',
                    'state', 'company_id', 'currency_id',
                    'fiscal_position_id', 'payment_term_id', 'dest_address_id',
                    'order_line', 'amount_total', 'amount_tax', 'amount_untaxed',
                ]])
                with open(os.path.join(export_dir, 'purchase_orders.json'), 'w') as f:
                    json.dump(purchases, f, indent=2, default=str)
                log(f"✅ Purchases: {len(purchases)}")
            
            # Export Stock Moves
            log("📦 Exporting Stock Moves...")
            move_ids = exec_kw('stock.move', 'search', [[
                ('date', '>=', str(cfg.start_date)),
                ('date', '<=', str(cfg.end_date)),
                ('state', '=', 'done'),
            ]], {'limit': 50000})
            
            if move_ids:
                moves = []
                for i in range(0, len(move_ids), 500):
                    batch = move_ids[i:i+500]
                    moves.extend(exec_kw('stock.move', 'read', [batch, [
                        'id', 'product_id', 'location_id', 'location_dest_id',
                        'picking_id', 'date', 'quantity', 'price_unit', 'state', 'company_id',
                    ]]))
                with open(os.path.join(export_dir, 'stock_moves.json'), 'w') as f:
                    json.dump(moves, f, indent=2, default=str)
                log(f"✅ Stock Moves: {len(moves)}")
            
            self.result = '\n'.join(log_lines)
            return {'type': 'ir.actions.act_window_close'}
            
        except Exception as e:
            raise UserError(f"Export failed: {str(e)}")
