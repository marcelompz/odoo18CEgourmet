{
    'name': 'Mass Import Suite',
    'version': '18.0.1.2.0',
    'category': 'Inventory/Products',
    'summary': 'Suite de importación masiva: productos y recetas',
    'description': """
        Mass Import Suite
        =================
        Agrupa los módulos de importación masiva en un solo lugar:

        * Product Mass Import (product_mass_import)
        * Excel Recipe Import (excel_recipe_import)

        Accesos directos desde el menú principal:
        - Productos: wizard de importación masiva con validación previa
        - Recetas: importador de recetas MRP y POS BoM desde Excel
    """,
    'author': 'Crossnexion E.A.S.',
    'website': 'https://www.crossnexion.com',
    'license': 'OPL-1',
    'depends': [
        'product_mass_import',
        'excel_recipe_import',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/suite_launcher_view.xml',
        'views/suite_menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
