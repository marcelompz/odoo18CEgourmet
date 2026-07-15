{
    'name': 'Reportes Contables Cross',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Reportes Financieros Avanzados para Odoo Community (P&L Estilo Enterprise)',
    'author': 'Crossnexion',
    'website': 'https://www.crossnexion.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/accounting_report_tag_views.xml',
        'views/accounting_report_views.xml',
        'views/accounting_report_wizard_views.xml',
        'views/account_move_line_views.xml',
        'views/menus.xml',
        'data/report_data.xml',
        'report/accounting_report_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'accounting_reporte_cross/static/src/css/report_styles.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
