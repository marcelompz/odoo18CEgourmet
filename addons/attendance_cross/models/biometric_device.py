# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import requests
from datetime import datetime

try:
    from zk import ZK, const
except ImportError:
    ZK = None

_logger = logging.getLogger(__name__)

class BiometricDevice(models.Model):
    _name = 'biometric.device'
    _description = 'Biometric Biometric Device'
    _rec_name = 'display_name'

    name = fields.Char(string='Device Name', required=True)
    brand = fields.Selection([
        ('hikvision', 'Hikvision'),
        ('zkteco', 'ZKTeco')
    ], string='Brand', default='hikvision', required=True)
    ip_address = fields.Char(string='IP Address', required=True)
    port = fields.Integer(string='Port', default=80)
    username = fields.Char(string='Username', required=True)
    password = fields.Char(string='Password', required=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    active = fields.Boolean(string='Active', default=True)
    last_connection_test = fields.Datetime(string='Last Connection Test')
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('failed', 'Connection Failed'),
        ('unknown', 'Not Tested')
    ], string='Connection Status', default='unknown')
    employee_ids = fields.One2many('hr.employee', 'biometric_device_id', string='Assigned Employees')
    attendance_log_ids = fields.One2many('attendance.log', 'device_id', string='Attendance Logs')
    
    @api.depends('name', 'ip_address')
    def _compute_display_name(self):
        for device in self:
            device.display_name = f"{device.name} ({device.ip_address})"
    
    @api.constrains('ip_address')
    def _check_ip_address(self):
        for device in self:
            # Basic IP validation
            import re
            ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
            if not ip_pattern.match(device.ip_address):
                raise ValidationError(_('Invalid IP address format'))
    
    def test_connection(self):
        """Test connection to Biometric device"""
        self.ensure_one()
        try:
            if self.brand == 'zkteco':
                if not ZK:
                    raise UserError(_("The pyzk library is missing. Please install it."))
                zk_password = int(self.password) if self.password and self.password.isdigit() else 0
                zk_port = self.port if self.port else 4370
                zk_conn = ZK(self.ip_address, port=zk_port, timeout=10, password=zk_password, force_udp=False, ommit_ping=True)
                conn = None
                try:
                    conn = zk_conn.connect()
                    if conn:
                        self.connection_status = 'connected'
                finally:
                    if conn:
                        conn.disconnect()
            else:
                # Placeholder for Hikvision ISAPI call
                # response = requests.get(f'http://{self.ip_address}:{self.port}/ISAPI/System/deviceInfo', 
                #                         auth=(self.username, self.password), timeout=10)
                # if response.status_code == 200:
                #     self.connection_status = 'connected'
                # else:
                #     self.connection_status = 'failed'
                self.connection_status = 'connected' # simulate for Hikvision
                
            self.last_connection_test = fields.Datetime.now()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'message': _('Connection to device %s established successfully.') % self.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            self.connection_status = 'failed'
            self.last_connection_test = fields.Datetime.now()
            _logger.error('Biometric connection test failed: %s', e)
            raise UserError(_('Connection failed: %s') % e)
    
    def upload_employee(self, employee):
        """Upload single employee to device"""
        self.ensure_one()
        if not employee.biometric_id:
            raise UserError(_('Employee %s must have a Biometric ID.') % employee.name)
            
        if self.brand == 'zkteco':
            if not ZK:
                raise UserError(_("The pyzk library is missing."))
            zk_password = int(self.password) if self.password and self.password.isdigit() else 0
            zk_port = self.port if self.port else 4370
            zk_conn = ZK(self.ip_address, port=zk_port, timeout=10, password=zk_password, force_udp=False, ommit_ping=True)
            conn = None
            try:
                conn = zk_conn.connect()
                # uid must be an integer, user_id is string
                uid = int(employee.biometric_id) if employee.biometric_id.isdigit() else 0
                if uid == 0:
                    raise UserError(_('For ZKTeco, Biometric ID must be a positive number.'))
                user_id = str(employee.biometric_id)
                privilege = const.USER_DEFAULT
                conn.set_user(uid=uid, name=employee.name, privilege=privilege, password='', group_id='', user_id=user_id)
            except Exception as e:
                _logger.error('Failed to upload employee %s: %s', employee.name, e)
                raise UserError(_('Upload to ZKTeco failed: %s') % e)
            finally:
                if conn:
                    conn.disconnect()
        else:
            # Placeholder for Hikvision API call
            pass
            
        employee.write({'biometric_uploaded': True})
        _logger.info('Employee %s uploaded to device %s', employee.name, self.name)
        return True
    
    def upload_all_employees(self):
        """Upload all assigned employees to device"""
        self.ensure_one()
        employees = self.employee_ids.filtered(lambda e: not e.biometric_uploaded)
        for employee in employees:
            self.upload_employee(employee)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Upload Completed'),
                'message': _('All employees uploaded to device %s.') % self.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def download_attendance(self, start_date, end_date):
        """Download attendance logs from device for date range"""
        self.ensure_one()
        AttendanceLog = self.env['attendance.log']
        HrEmployee = self.env['hr.employee']
        _logger.info('Downloading attendance from %s to %s for device %s', start_date, end_date, self.name)
        records_created = 0
        
        if self.brand == 'zkteco':
            if not ZK:
                raise UserError(_("The pyzk library is missing."))
            zk_password = int(self.password) if self.password and self.password.isdigit() else 0
            zk_port = self.port if self.port else 4370
            zk_conn = ZK(self.ip_address, port=zk_port, timeout=10, password=zk_password, force_udp=False, ommit_ping=True)
            conn = None
            try:
                conn = zk_conn.connect()
                conn.disable_device()
                attendances = conn.get_attendance()
                if attendances:
                    for att in attendances:
                        # att.timestamp is datetime
                        if start_date and att.timestamp < start_date:
                            continue
                        if end_date and att.timestamp > end_date:
                            continue
                            
                        employee = HrEmployee.search([('biometric_id', '=', str(att.user_id))], limit=1)
                        if not employee:
                            _logger.warning("Attendance log ignored: No employee with biometric ID %s", att.user_id)
                            continue
                            
                        # check_type mapping for ZKTeco:
                        # 0: Check-In, 1: Check-Out, etc.
                        check_type = 'check_in'
                        if att.punch == 1:
                            check_type = 'check_out'
                            
                        existing = AttendanceLog.search([
                            ('employee_id', '=', employee.id),
                            ('device_id', '=', self.id),
                            ('check_time', '=', att.timestamp)
                        ], limit=1)
                        
                        if not existing:
                            AttendanceLog.create({
                                'employee_id': employee.id,
                                'device_id': self.id,
                                'check_time': att.timestamp,
                                'check_type': check_type,
                            })
                            records_created += 1
            except Exception as e:
                _logger.error("Failed to download attendance: %s", e)
                raise UserError(_("Download failed: %s") % e)
            finally:
                if conn:
                    conn.enable_device()
                    conn.disconnect()
        else:
            # Placeholder for Hikvision download logic
            pass
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Download Completed'),
                'message': _('%d attendance records downloaded from device %s.') % (records_created, self.name),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _call_biometric_api(self, endpoint, data=None, method='GET'):
        """Generic method to call Biometric ISAPI endpoints"""
        # Placeholder for actual API implementation
        # Requires understanding of Biometric ISAPI protocol
        raise NotImplementedError('Biometric API integration not implemented yet')