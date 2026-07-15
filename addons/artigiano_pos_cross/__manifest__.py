# -*- coding: utf-8 -*-
#MANIFEST FILE

{
    'name': 'Crossnexion - Cerrar sesión',
    'summary': 'Ocultar campos en la vista de Cerrar sesión',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Point of Sale',
    'version': '25.8.4',
    'depends': ['point_of_sale','pos_restaurant'],
    'data': [],
    'assets': {
    'point_of_sale._assets_pos': [
            'artigiano_pos_cross/static/src/xml/close_pos_popup.xml',
            'artigiano_pos_cross/static/src/xml/pos_order_receipt.xml',
            'artigiano_pos_cross/static/src/js/pos_order_model.js',
        ],
    },
}
