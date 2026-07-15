# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MigrationCloneWizard(models.TransientModel):
    _name = 'migration.clone.wizard'
    _description = 'Clone and Clean Database'

    config_id = fields.Many2one('migration.config', string='Configuration', required=True)
    source_db = fields.Char(string='Source Database', required=True)
    target_db = fields.Char(string='Target Database', required=True)
    result = fields.Text(string='Result', readonly=True)
    
    @api.onchange('config_id')
    def _onchange_config(self):
        if self.config_id:
            self.source_db = self.config_id.source_db
            self.target_db = self.config_id.target_db
    
    def action_clone_and_clean(self):
        self.ensure_one()
        try:
            result = self.config_id.clone_and_clean_db(self.source_db, self.target_db)
            self.result = result
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'migration.clone.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
                'name': _('Clone Result'),
            }
        except Exception as e:
            raise UserError(str(e))
