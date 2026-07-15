# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class UploadEmployeesWizard(models.TransientModel):
    _name = 'upload.employees.wizard'
    _description = 'Upload Employees to Biometric Device Wizard'
    
    device_id = fields.Many2one('biometric.device', string='Device', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    upload_all = fields.Boolean(string='Upload All Employees', default=True)
    
    @api.onchange('device_id')
    def _onchange_device_id(self):
        if self.device_id and self.upload_all:
            employees = self.env['hr.employee'].search([
                ('biometric_device_id', '=', self.device_id.id),
                ('biometric_uploaded', '=', False)
            ])
            self.employee_ids = employees
    
    def action_upload(self):
        self.ensure_one()
        if not self.device_id:
            raise ValidationError(_('Please select a device'))
        
        if self.upload_all:
            employees = self.env['hr.employee'].search([
                ('biometric_device_id', '=', self.device_id.id),
                ('biometric_uploaded', '=', False)
            ])
        else:
            employees = self.employee_ids
        
        if not employees:
            raise ValidationError(_('No employees to upload'))
        
        success_count = 0
        error_count = 0
        
        for employee in employees:
            try:
                self.device_id.upload_employee(employee)
                success_count += 1
            except Exception as e:
                error_count += 1
                _logger.error('Failed to upload employee %s: %s', employee.name, e)
        
        message = _('%s employees uploaded successfully.') % success_count
        if error_count:
            message += _(' %s employees failed to upload.') % error_count
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upload Completed'),
                'message': message,
                'type': 'success' if error_count == 0 else 'warning',
                'sticky': True,
            }
        }