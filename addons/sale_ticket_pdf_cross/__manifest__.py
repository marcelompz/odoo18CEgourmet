# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Cotizaciones en ticket PDF (80mm)',
    'summary': 'Este módulo genera un PDF en formato ticket de la cotización',
    'description': """
        - genera un PDF en formato ticket de la cotización
    """,
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Sales',
    'version': '25.11.22',
    'depends': [
        'sale',
    ],
    'data': [
        'data/paper_format.xml',
        'reports/sale_ticket_report.xml',
    ],
}
