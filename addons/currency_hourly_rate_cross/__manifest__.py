{
    'name': 'Currency Hourly Rate',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Registrar tipo de cambio por hora y acceso directo a Monedas',
    'description': '''
        Extiende res.currency para registrar tasas de cambio por hora.
        Agrega un ícono de acceso directo al listado de Monedas.
    ''',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_currency_hourly_rate_views.xml',
        'views/res_currency_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
