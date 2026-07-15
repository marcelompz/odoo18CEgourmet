# -*- coding: utf-8 -*-
{
    'name': "Biometric Attendance Integration",
    'version': '18.0.1.0.1',
    'category': 'Human Resources',
    'summary': 'Integración con dispositivos biométricos Biometric para gestión de asistencia',
    'description': """
        Módulo para sincronizar empleados y registros de asistencia entre Odoo y dispositivos biométricos Biometric.
        Permite registro individual y masivo de empleados, descarga de asistencias y generación de informes Excel.
    """,
    'author': 'Crossnexion EAS',
    'website': 'https://www.crossnexion.com',
    'depends': ['base', 'hr', 'hr_attendance', 'web', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/biometric_device_views.xml',
        'views/hr_employee_views.xml',
        'views/attendance_log_views.xml',
        'wizards/upload_employees_wizard_views.xml',
        'wizards/download_attendance_wizard_views.xml',
        'wizards/attendance_report_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
}