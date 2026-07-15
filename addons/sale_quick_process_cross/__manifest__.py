# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Proceso de venta rápida',
    'summary': 'Añade un botón para entregar y facturar ventas rápidamente.',
    'description': '''
        - Añade un botón para entregar y facturar ventas rápidamente.
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Sales',
    'version': '25.11.23',
    'depends': [
        'sale_management',
        'stock',
        'account',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order.xml',
    ],
}
