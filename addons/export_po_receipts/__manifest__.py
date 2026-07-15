{
    'name': 'Export Purchase Receipts Data',
    'version': '1.0',
    'category': 'Purchases',
    'summary': 'Export Purchase Orders with their Receipt Lots and Expiration Dates',
    'depends': ['purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/export_wizard_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
