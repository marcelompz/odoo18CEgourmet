{
    'name': 'Sales Automation Cross',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Automatiza la confirmación de ventas, creación de facturas, registro de pagos y validación de entregas (Ventas y POS).',
    'description': """
        Este módulo proporciona una acción de servidor para automatizar el flujo completo de una orden de venta y pedidos de POS:
        1. Confirma la orden.
        2. Crea y valida la factura.
        3. Registra el pago de la factura.
        4. Valida la salida de mercancía (picking).
    """,
    'author': 'Crossnexion',
    'depends': ['sale_management', 'account', 'stock', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/pos_order_views.xml',
        'wizard/pos_order_import_wizard_view.xml',
        'data/server_action.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
