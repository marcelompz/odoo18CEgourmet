# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Margen de ventas con impuestos incluidos',
    'summary': 'Calcula el margen de ventas incluyendo impuestos.',
    'description': '''
        - Se agrega boton para recalcular margen en las ordenes de ventas
        - Se agrega grupo de usuario para vista exclusiva de los margenes de ventas
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Sales/Sales',
    'version': '25.11.16',
    'depends': [
        'sale_margin',
        'sale'
    ],
    'data': [
        'security/res_groups.xml',
        'data/ir_actions_server.xml',
        'views/sale_order.xml',
    ],
}
