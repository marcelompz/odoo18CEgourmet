# -*- coding: utf-8 -*-
{
    'name': 'POS Printing Odoo 18',
    'category': 'Point of Sale',
    'summary': 'Connects Point of Sale to local printer server on Odoo 18',
    'description': 'Direct printing for tickets and invoices in Odoo 18 CE',
    'author': 'Crossnexion',
    'version': '18.0.1.0',
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'printing/static/src/js/Printing.js',
            'printing/static/src/xml/OrderReceipt.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
