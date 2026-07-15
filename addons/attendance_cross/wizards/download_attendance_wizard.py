# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class DownloadAttendanceWizard(models.TransientModel):
    _name = 'download.attendance.wizard'
    _description = 'Download Attendance from Biometric Device Wizard'
    
    device_id = fields.Many2one('biometric.device', string='Device', required=True)
    start_date = fields.Datetime(string='Start Date', required=True, default=lambda self: fields.Datetime.now() - timedelta(days=1))
    end_date = fields.Datetime(string='End Date', required=True, default=lambda self: fields.Datetime.now())
    clear_existing = fields.Boolean(string='Clear Existing Logs', help='Delete existing logs for the selected period before downloading', default=False)
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for wizard in self:
            if wizard.start_date > wizard.end_date:
                raise ValidationError(_('Start date cannot be after end date'))
            if wizard.end_date > fields.Datetime.now():
                raise ValidationError(_('End date cannot be in the future'))
    
    def action_download(self):
        self.ensure_one()
        if not self.device_id:
            raise ValidationError(_('Please select a device'))
        
        # Clear existing logs if requested
        if self.clear_existing:
            existing_logs = self.env['attendance.log'].search([
                ('device_id', '=', self.device_id.id),
                ('check_time', '>=', self.start_date),
                ('check_time', '<=', self.end_date)
            ])
            if existing_logs:
                existing_logs.unlink()
        
        try:
            # Download attendance from device
            self.device_id.download_attendance(self.start_date, self.end_date)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Download Completed'),
                    'message': _('Attendance records downloaded from %s to %s.') % (self.start_date, self.end_date),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise ValidationError(_('Download failed: %s') % e)