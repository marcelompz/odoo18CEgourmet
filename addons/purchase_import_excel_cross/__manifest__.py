# -*- coding: utf-8 -*-
{
    'name': 'Crossnexion - Importar Compras desde Excel',
    'summary': 'Importa órdenes de compra desde una planilla Excel, incluyendo lotes y fechas de caducidad.',
    'description': '''
        Permite importar una planilla Excel en el módulo de compras con los siguientes campos:
        - Datos del proveedor
        - Fecha de la compra
        - Datos del producto (nombre/código)
        - Cantidad
        - Costo (precio unitario)
        - Impuesto
        - Margen (porcentaje sobre el costo para precio de venta)
        - Número de lote / Serie
        - Fecha de caducidad

        Al confirmar y recepcionar la orden, los lotes y fechas de caducidad se asignan
        automáticamente a los movimientos de stock correspondientes.
    ''',
    'author': 'Crossnexion EAS',
    'website': 'www.crossnexion.com',
    'license': 'OPL-1',
    'category': 'Purchase',
    'version': '18.0.1.0.0',
    'depends': [
        'purchase',
        'purchase_stock',
        'stock',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_import_wizard_views.xml',
        'views/purchase_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
