# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Bloqueo de venta costo cero',
    'summary': 'Impide vender productos con costo cero en el POS',
    'description': '''
        - Impide vender productos con costo cero en el POS
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Point of Sale',
    'version': '26.2.9',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        # 'security/ir.model.access.csv',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_block_zero_cost_cross/static/src/js/payment_screen.js',
        ],
    },
}
