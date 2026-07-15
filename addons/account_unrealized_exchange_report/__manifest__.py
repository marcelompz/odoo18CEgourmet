{
    'name': 'Reporte de Ganancias/Pérdidas no Realizadas',
    'version': '18.0.1.0.1',
    'category': 'Accounting/Localizations',
    'summary': 'Reporte de ganancias y pérdidas no realizadas por cambio de divisa',
    'description': """
    Módulo para generar el reporte de ganancias y pérdidas no realizadas por diferencia de tipo de cambio en Odoo 18.
    Incluye:
    - Evaluación de facturas, pagos y movimientos bancarios abiertos.
    - Tipo de cambio original vs actual.
    - Ganancias y pérdidas por moneda.
    - Filtros por fecha, moneda, tipo de movimiento.
    - Exportación y vista pivote/gráfico.
    """,
    'author': 'Crossnexion Tools',
    'website': 'https://crossnexion.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/unrealized_exchange_wizard_views.xml',
        'views/unrealized_exchange_report_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
