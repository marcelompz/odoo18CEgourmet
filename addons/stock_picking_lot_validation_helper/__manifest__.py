# -*- coding: utf-8 -*-
{
    'name': "Crossnexion - Stock Picking Lot Validation Helper",
    'summary': """
        Extiende la validación de recepciones para identificar el producto con error de lote/serie.
        Muestra un mensaje de error más específico al validar un albarán si falta el lote/serie.
    """,
    'description': """
        Este módulo modifica el comportamiento de la validación de movimientos de stock
        para proporcionar un feedback más detallado cuando un producto requiere un
        número de lote o serie, pero no ha sido proporcionado en la línea de movimiento.
        Esto es útil para depurar errores de "Operación no válida".
    """,
    'author': "Crossnexion E. A. S.",
    'website': "https://www.crossnexion.com",
    'category': 'Inventory/Inventory',
    'version': '1.0',
    'license': 'OPL-1',
    'depends': ['stock'],
    'data': [
        # No hay vistas ni seguridad adicional en este módulo, solo lógica.
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
