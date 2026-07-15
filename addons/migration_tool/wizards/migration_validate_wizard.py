# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MigrationValidateWizard(models.TransientModel):
    _name = 'migration.validate.wizard'
    _description = 'Validate Migration'

    config_id = fields.Many2one('migration.config', string='Configuration', required=True)
    result = fields.Text(string='Result', readonly=True)
    
    def action_validate(self):
        self.ensure_one()
        cfg = self.config_id
        log_lines = []
        
        def log(msg):
            log_lines.append(msg)
            _logger.info(msg)
        
        log("🔍 Validating migration...")
        log(f"Source: {cfg.source_db}")
        log(f"Target: {cfg.target_db}")
        log(f"Type: {cfg.deployment_type}")
        log("")
        
        tables = [
            'purchase_order', 'purchase_order_line',
            'pos_order', 'pos_order_line', 'pos_payment',
            'stock_picking', 'stock_move', 'stock_move_line',
            'stock_quant', 'stock_valuation_layer',
        ]
        
        for table in tables:
            r_src = cfg._run_psql(cfg.source_db, f"SELECT COUNT(*) FROM {table};")
            r_dst = cfg._run_psql(cfg.target_db, f"SELECT COUNT(*) FROM {table};")
            
            src_count = r_src.stdout.strip().split('\n')[2].strip() if len(r_src.stdout.strip().split('\n')) > 2 else '?'
            dst_count = r_dst.stdout.strip().split('\n')[2].strip() if len(r_dst.stdout.strip().split('\n')) > 2 else '?'
            
            if src_count == dst_count:
                log(f"✅ {table}: {src_count} = {dst_count}")
            else:
                log(f"❌ {table}: source={src_count} ≠ target={dst_count}")
        
        # Check PO amounts
        r_src = cfg._run_psql(cfg.source_db, "SELECT COALESCE(SUM(amount_total),0) FROM purchase_order;")
        r_dst = cfg._run_psql(cfg.target_db, "SELECT COALESCE(SUM(amount_total),0) FROM purchase_order;")
        
        src_total = r_src.stdout.strip().split('\n')[2].strip() if len(r_src.stdout.strip().split('\n')) > 2 else '?'
        dst_total = r_dst.stdout.strip().split('\n')[2].strip() if len(r_dst.stdout.strip().split('\n')) > 2 else '?'
        log(f"\n💰 PO Total - Source: {src_total} | Target: {dst_total}")
        
        # Check POS amounts
        r_src = cfg._run_psql(cfg.source_db, "SELECT COALESCE(SUM(amount_total),0) FROM pos_order;")
        r_dst = cfg._run_psql(cfg.target_db, "SELECT COALESCE(SUM(amount_total),0) FROM pos_order;")
        
        src_pos = r_src.stdout.strip().split('\n')[2].strip() if len(r_src.stdout.strip().split('\n')) > 2 else '?'
        dst_pos = r_dst.stdout.strip().split('\n')[2].strip() if len(r_dst.stdout.strip().split('\n')) > 2 else '?'
        log(f"💰 POS Total - Source: {src_pos} | Target: {dst_pos}")
        
        # Check SVL value
        r_src = cfg._run_psql(cfg.source_db, "SELECT COALESCE(SUM(value),0)::text FROM stock_valuation_layer;")
        r_dst = cfg._run_psql(cfg.target_db, "SELECT COALESCE(SUM(value),0)::text FROM stock_valuation_layer;")
        
        src_svl = r_src.stdout.strip().split('\n')[2].strip() if len(r_src.stdout.strip().split('\n')) > 2 else '?'
        dst_svl = r_dst.stdout.strip().split('\n')[2].strip() if len(r_dst.stdout.strip().split('\n')) > 2 else '?'
        log(f"💰 SVL Value - Source: {src_svl} | Target: {dst_svl}")
        
        self.result = '\n'.join(log_lines)
        return {'type': 'ir.actions.act_window_close'}
