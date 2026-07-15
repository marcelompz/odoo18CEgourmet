# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import csv
import io
import base64
import json


class CleanupExportWizard(models.TransientModel):
    _name = 'cleanup.export.wizard'
    _description = 'Cleanup Export Wizard'
    
    log_id = fields.Many2one('cleanup.log', string='Cleanup Log', required=True, readonly=True)
    
    export_format = fields.Selection([
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ], string='Export Format', default='csv', required=True)
    
    include_details = fields.Boolean(string='Include Detailed Values', default=True,
        help='Include old/new values in export')
    
    file_name = fields.Char(string='File Name', compute='_compute_file_name')
    data = fields.Binary(string='File', readonly=True)
    
    @api.depends('log_id', 'export_format')
    def _compute_file_name(self):
        for wizard in self:
            name = wizard.log_id.name or 'cleanup_log'
            wizard.file_name = f'{name}.{wizard.export_format}'
    
    @api.model
    def default_get(self, fields_list):
        defaults = super(CleanupExportWizard, self).default_get(fields_list)
        context = self.env.context
        
        if 'default_log_id' in context:
            defaults['log_id'] = context['default_log_id']
        
        return defaults
    
    def action_export(self):
        self.ensure_one()
        
        if self.export_format == 'csv':
            data = self._generate_csv()
        else:
            data = self._generate_json()
        
        self.write({'data': base64.b64encode(data)})
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content?model={self._name}&id={self.id}&field=data&filename={self.file_name}&download=true',
            'target': 'self',
        }
    
    def _generate_csv(self):
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Write header
        headers = [
            'ID', 'Model', 'Record ID', 'Record Name', 'Action Type', 'Discrepancy Type',
            'Original User', 'Original Create Date', 'Execution Date', 'Status',
        ]
        
        if self.include_details:
            headers.extend(['Old Values', 'New Values'])
        
        writer.writerow(headers)
        
        # Write rows
        for line in self.log_id.log_line_ids:
            row = [
                line.id,
                line.model_name,
                line.record_id,
                line.record_name or '',
                line.action_type,
                line.discrepancy_type or '',
                line.original_user_id.name if line.original_user_id else '',
                line.original_create_date or '',
                line.execution_date or '',
                line.status,
            ]
            
            if self.include_details:
                row.extend([
                    line.old_values or '',
                    line.new_values or '',
                ])
            
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    def _generate_json(self):
        log_data = {
            'log': {
                'id': self.log_id.id,
                'name': self.log_id.name,
                'execution_date': self.log_id.execution_date.isoformat() if self.log_id.execution_date else None,
                'executed_by': self.log_id.executed_by.name if self.log_id.executed_by else None,
                'config': self.log_id.config_id.name if self.log_id.config_id else None,
                'status': self.log_id.status,
                'lines': [],
            }
        }
        
        for line in self.log_id.log_line_ids:
            line_data = {
                'id': line.id,
                'model': line.model_name,
                'record_id': line.record_id,
                'record_name': line.record_name,
                'action_type': line.action_type,
                'discrepancy_type': line.discrepancy_type,
                'original_user': line.original_user_id.name if line.original_user_id else None,
                'original_create_date': line.original_create_date.isoformat() if line.original_create_date else None,
                'execution_date': line.execution_date.isoformat() if line.execution_date else None,
                'status': line.status,
            }
            
            if self.include_details:
                try:
                    line_data['old_values'] = json.loads(line.old_values) if line.old_values else None
                    line_data['new_values'] = json.loads(line.new_values) if line.new_values else None
                except (json.JSONDecodeError, TypeError):
                    line_data['old_values'] = line.old_values
                    line_data['new_values'] = line.new_values
            
            log_data['log']['lines'].append(line_data)
        
        return json.dumps(log_data, indent=2, default=str).encode('utf-8')
    
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}