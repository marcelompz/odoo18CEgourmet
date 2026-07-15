# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Proceso de compra rápida',
    'summary': 'Añade un botón para recepcionar y facturar compras rápidamente.',
    'description': '''
        - Añade un botón para recepcionar y facturar compras rápidamente.
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Purchases',
    'version': '25.11.23',
    'depends': [
        'purchase',
        'stock',
        'account',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_order.xml',
    ],
}
