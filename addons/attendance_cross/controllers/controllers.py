# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class BiometricAttendanceController(http.Controller):
    
    @http.route('/biometric/device/<int:device_id>/test', type='http', auth='user')
    def test_device_connection(self, device_id, **kwargs):
        """Test device connection via web interface"""
        device = request.env['biometric.device'].browse(device_id)
        if not device.exists():
            return request.not_found()
        
        try:
            device.test_connection()
            return request.redirect('/web#id=%s&model=biometric.device&view_type=form' % device_id)
        except Exception as e:
            return request.render('attendance_cross.connection_error', {
                'error': str(e),
                'device': device
            })
    
    @http.route('/biometric/attendance/report/download', type='http', auth='user')
    def download_attendance_report(self, **kwargs):
        """Download attendance report"""
        # This would generate and serve a report file
        pass