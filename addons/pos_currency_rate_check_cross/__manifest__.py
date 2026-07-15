# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - PoS - Verificación de Tasa de Cambio',
    'summary': 'Impide abrir una caja de PoS si las tasas de cambio del día no están cargadas.',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Sales/Point of Sale',
    'version': '25.9.25',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/currency_rate_warning_wizard.xml',
    ],
}
