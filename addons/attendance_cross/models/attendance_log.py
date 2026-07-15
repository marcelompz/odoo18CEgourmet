# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AttendanceLog(models.Model):
    _name = 'attendance.log'
    _description = 'Attendance Log from Biometric Device'
    _order = 'check_time desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    device_id = fields.Many2one('biometric.device', string='Device', required=True)
    check_time = fields.Datetime(string='Check Time', required=True)
    check_type = fields.Selection([
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ('break_start', 'Break Start'),
        ('break_end', 'Break End')
    ], string='Check Type', default='check_in')
    biometric_id = fields.Char(string='Biometric ID', related='employee_id.biometric_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', store=True)
    processed = fields.Boolean(string='Processed', default=False)
    notes = fields.Text(string='Notes')
    
    @api.constrains('check_time')
    def _check_check_time(self):
        for log in self:
            if log.check_time > fields.Datetime.now():
                raise ValidationError(_('Check time cannot be in the future'))
    
    def process_attendance(self):
        """Process attendance log into Odoo hr.attendance records"""
        self.ensure_one()
        HrAttendance = self.env['hr.attendance']
        
        if self.processed:
            _logger.warning('Attendance log already processed: %s', self.id)
            return False
        
        # Find existing attendance records for this employee
        existing_attendance = HrAttendance.search([
            ('employee_id', '=', self.employee_id.id),
            ('check_in', '<=', self.check_time),
            '|', ('check_out', '=', False), ('check_out', '>=', self.check_time)
        ], limit=1)
        
        if self.check_type in ('check_in', 'break_end'):
            # Create new attendance record or update existing
            if existing_attendance:
                # Update existing record if check_out is not set
                if not existing_attendance.check_out:
                    existing_attendance.write({'check_out': self.check_time})
                    new_record = HrAttendance.create({
                        'employee_id': self.employee_id.id,
                        'check_in': self.check_time,
                    })
                else:
                    # Create new record
                    new_record = HrAttendance.create({
                        'employee_id': self.employee_id.id,
                        'check_in': self.check_time,
                    })
            else:
                new_record = HrAttendance.create({
                    'employee_id': self.employee_id.id,
                    'check_in': self.check_time,
                })
        
        elif self.check_type in ('check_out', 'break_start'):
            # Set check_out on existing open attendance
            if existing_attendance and not existing_attendance.check_out:
                existing_attendance.write({'check_out': self.check_time})
            else:
                # Create a check_in record if none exists
                HrAttendance.create({
                    'employee_id': self.employee_id.id,
                    'check_in': self.check_time,
                    'check_out': self.check_time,
                })
        
        self.processed = True
        _logger.info('Processed attendance log %s for employee %s', self.id, self.employee_id.name)
        return True
    
    def process_all(self):
        """Process all unprocessed attendance logs"""
        unprocessed = self.search([('processed', '=', False)])
        for log in unprocessed:
            try:
                log.process_attendance()
            except Exception as e:
                _logger.error('Failed to process attendance log %s: %s', log.id, e)
                log.write({'notes': f'Processing failed: {e}'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Processing Completed'),
                'message': _('%s attendance logs processed.') % len(unprocessed),
                'type': 'success',
                'sticky': False,
            }
        }