# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Informe de ventas y rentabilidad',
    'summary': 'Generar informes de ventas y rentabilidad por usuario dentro de un rango de fechas.',
    'description': """
        Este módulo permite generar reportes de ventas y rentabilidad filtrados por usuario y un rango de fechas específico.
    """,
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Uncategorized',
    'version': '26.1.15',
    'depends': [
        'sale_margin',
    ],
    'data': [
        'data/custompaperformat.xml',
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'reports/commercial_report.xml',
        'wizard/report_date_range_wizard.xml',
    ],
}
