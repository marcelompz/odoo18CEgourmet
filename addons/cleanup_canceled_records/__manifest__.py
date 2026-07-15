# -*- coding: utf-8 -*-
{
    'name': "Cleanup Canceled Records",
    'version': '18.0.1.0.4',
    'category': 'Tools',
    'summary': 'Cancel and delete inventory moves, purchases and invoices in blocked or canceled state',
    'description': """
        This module allows to cancel and delete records in blocked or canceled state.
        Supports inventory moves, purchase orders and invoices.
        Provides configuration and wizard to execute cleanup actions.
        Includes POS tax correction and tax assignment by category features.
    """,
    'author': "Crossnexion E. A. S.",
    'license': 'OPL-1',
    'website': "https://www.crossnexion.com",
    'depends': ['base', 'stock', 'purchase', 'account', 'product', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/cleanup_config_data.xml',
        'data/cleanup_sequence_data.xml',
        'views/cleanup_config_views.xml',
        'views/cleanup_log_views.xml',
        'wizard/cleanup_wizard_views.xml',
        'wizard/cleanup_pos_tax_wizard_views.xml',
        'wizard/cleanup_revert_wizard_views.xml',
        'wizard/cleanup_export_wizard_views.xml',
        'wizard/cleanup_tax_assignment_wizard_views.xml',
        # 'data/ir_cron_data.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
} # type: ignore