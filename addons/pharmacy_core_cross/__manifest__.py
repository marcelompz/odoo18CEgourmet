# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Farmacia',
    'summary': 'Ajustes base y reglas específicas para el rubro farmacia.',
    'description': '''
        - Ajustes base y reglas específicas para el rubro farmacia.
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Uncategorized',
    'version': '26.1.21',
    'depends': [
        'base',
        'product',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_brand.xml',
        'views/product_laboratory.xml',
        'views/product_template.xml',
        'views/sale_report.xml',
    ],
}
