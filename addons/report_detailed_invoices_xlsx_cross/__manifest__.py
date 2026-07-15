# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Reporte Detallado de Facturas, Compras y Cotizaciones en Excel',
    'summary': '''
        Genera un reporte de Excel con el detalle de las líneas de facturas y notas de crédito de clientes, además de las líneas de compras y cotizaciones.
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Accounting/Reporting',
    'version': '26.1.8',
    'depends': [
        'account',
        'electronic_invoice_cross',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/detailed_invoices_report_wizard.xml',
        'wizard/detailed_quotations_report_wizard.xml',
        'wizard/detailed_purchases_report_wizard.xml',
    ],
}
