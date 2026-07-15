{
    'name': 'Módulo de corrección de datos e impuestos',
    'version': '18.0.1.14.0',
    'category': 'Accounting/Localizations',
    'summary': 'Detecta y corrige inconsistencias de impuestos y datos maestros en ítems.',
    'description': '''
        Este módulo permite auditar de forma masiva las facturas de compras, ventas y sesiones de punto de venta (PdV) 
        para identificar si los impuestos aplicados o atributos (como lotes) coinciden con la configuración 
        actual de la tabla maestra de ítems (productos/servicios).
    ''',
    'author': 'Crossnexion EAS',
    'depends': ['base', 'product', 'account', 'purchase', 'sale', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/inconsistency_views.xml',
        'views/history_views.xml',
        'wizards/mass_tax_update_wizard_views.xml',
        'wizards/mass_history_tax_clear_wizard_views.xml',
        'wizards/force_draft_wizard_views.xml',
        'wizards/dashboard_wizard_views.xml',
        'views/data_correction_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
} # pyright: ignore[reportUnusedExpression]