{
    'name': 'POS Multi Currency',
    'version': '26.2.18',
    'category': 'Point of Sale',
    'summary': 'POS Multi Currency with DPS Cash Control compatibility',
    'description': 'POS Multi Currency - Enhanced compatibility with dps_pos_multi_currency_cashcontrol',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'depends': [
        'point_of_sale',
        'dps_pos_multi_currency_cashcontrol',
    ],
    'data': [
        'views/pos_order_view.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_multi_currency/static/src/css/payment_screen.css',
            'pos_multi_currency/static/src/js/compatibility_check.js',
            'pos_multi_currency/static/src/js/payment_screen.js',
            'pos_multi_currency/static/src/js/pos_payment.js',
            'pos_multi_currency/static/src/js/payment_status.js',
            'pos_multi_currency/static/src/xml/payment_screen.xml',
            'pos_multi_currency/static/src/xml/payment_lines.xml',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
