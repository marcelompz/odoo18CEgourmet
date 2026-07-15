{
    'name': 'Monedas (Acceso Directo Visible)',
    'version': '1.0',
    'category': 'Invoicing',
    'summary': 'Adds a visible menu entry and direct shortcut to the list of Currencies.',
    'description': """
        This module creates a direct, visible menu item to access the list view of Currencies (res.currency), 
        enhancing user accessibility within Odoo Community Edition's Invoicing application. 
        It provides an explicit entry point beyond the global search (Ctrl+K).
    """,
    'author': 'Crossnexion E. A. S.',
    'website': 'crossnexion.com',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/currency_shortcut_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
