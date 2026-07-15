# -*- coding: utf-8 -*-
import os
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MigrationImportWizard(models.TransientModel):
    _name = 'migration.import.wizard'
    _description = 'Import Transactions'

    config_id = fields.Many2one('migration.config', string='Configuration', required=True)
    export_path = fields.Char(string='Export Path', related='config_id.export_path')
    result = fields.Text(string='Result', readonly=True)
    
    def action_import(self):
        self.ensure_one()
        cfg = self.config_id
        log_lines = []
        
        def log(msg):
            log_lines.append(msg)
            _logger.info(msg)
        
        try:
            # Import all transactional tables via unified method
            log("📥 Importing transactional data...")
            log_lines.append(cfg.copy_all_transactional(cfg.source_db, cfg.target_db))
            
            self.result = '\n'.join(log_lines)
            return {'type': 'ir.actions.act_window_close'}
            
        except Exception as e:
            raise UserError(f"Import failed: {str(e)}")
