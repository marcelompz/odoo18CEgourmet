# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    biometric_id = fields.Char(string='Biometric ID', help='Unique ID used in Biometric device')
    biometric_device_id = fields.Many2one('biometric.device', string='Assigned Biometric Device')
    biometric_uploaded = fields.Boolean(string='Uploaded to Device', default=False)
    attendance_log_ids = fields.One2many('attendance.log', 'employee_id', string='Attendance Logs')
    
    def action_upload_to_device(self):
        """Upload employee to assigned Biometric device"""
        self.ensure_one()
        if not self.biometric_device_id:
            raise ValidationError(_('No Biometric device assigned to this employee'))
        
        if not self.biometric_id:
            raise ValidationError(_('Biometric ID is required for device upload'))
        
        try:
            self.biometric_device_id.upload_employee(self)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Upload Successful'),
                    'message': _('Employee %s uploaded to device %s.') % (self.name, self.biometric_device_id.name),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise ValidationError(_('Upload failed: %s') % e)
    
    @api.constrains('biometric_id')
    def _check_biometric_id_unique(self):
        for employee in self:
            if employee.biometric_id:
                existing = self.search([
                    ('biometric_id', '=', employee.biometric_id),
                    ('id', '!=', employee.id)
                ])
                if existing:
                    raise ValidationError(_('Biometric ID must be unique. Already used by employee %s') % existing.name)
    
    def action_view_attendance_logs(self):
        """View attendance logs for this employee"""
        self.ensure_one()
        action = self.env.ref('attendance_cross.action_attendance_log').read()[0]
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {'default_employee_id': self.id, 'search_default_employee_id': self.id}
        return action