# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - POS Report',
    'summary': 'POS Sales Detail Report (Fixed)',
    'description': '''
        - POS Sales Detail Report (Fixed)
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_wizard_view.xml',
        'report/pos_sales_report.xml',
    ],
}
