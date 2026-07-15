# -*- coding: utf-8 -*-
{
    'name': 'Migration Tool',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Clone, clean, export, import and validate Odoo databases',
    'description': """
Migration Tool
==============
Provides wizards to:
- Clone and clean a database (backup, truncate transactional tables)
- Export transactions (purchases, POS, stock moves)
- Import transactions into a clean database
- Validate inventory and data consistency

Supports Odoo 18 with Docker Compose deployments.
    """,
    'author': 'Crossnexion E.A.S.',
    'license': 'OPL-1',
    'website': 'https://www.crossnexion.com',
    'depends': ['base', 'stock', 'purchase', 'account', 'sale', 'point_of_sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/migration_clone_wizard_views.xml',
        'wizards/migration_export_wizard_views.xml',
        'wizards/migration_import_wizard_views.xml',
        'wizards/migration_validate_wizard_views.xml',
        'wizards/migration_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
