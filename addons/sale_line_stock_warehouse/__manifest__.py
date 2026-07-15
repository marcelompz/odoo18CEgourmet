# -*- coding: utf-8 -*-
{
    'name': 'Stock en Línea de Venta Mejorado',
    'summary': 'Muestra stock de todos los almacenes en la línea de venta con interfaz moderna',
    'description': '''
        Módulo mejorado para Odoo 18 que muestra el stock disponible en todos los almacenes
        directamente en las líneas de venta. Utiliza componentes modernos de Odoo 18
        y evita la manipulación directa del DOM para garantizar compatibilidad.
        
        Características:
        - Stock por almacén en tiempo real
        - Interfaz moderna y responsive
        - Compatible con campos many2one
        - Sin JavaScript crudo
        - Optimizado para Odoo 18
    ''',
    'author': 'Ing. Daril Diaz',
    'website': '',
    'license': 'LGPL-3',
    'category': 'Sales/Sales',
    'version': '26.1.27',
    'depends': [
        'base',
        'web',
        'sale',
        'sale_stock',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/stock_warehouse_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Extensión del popup de disponibilidad (inyecta HTML dinámicamente, NO usa XML)
            # Se carga DESPUÉS de sale_stock para tener acceso a QtyAtDateWidget
            ('after', 'sale_stock/static/src/widgets/**/*', 'sale_line_stock_warehouse/static/src/js/qty_at_date_popover_extension.js'),
            
            # Widget de información de stock (opcional, para uso futuro)
            'sale_line_stock_warehouse/static/src/js/stock_info_widget.js',
            'sale_line_stock_warehouse/static/src/xml/stock_info_widget.xml',
            
            # Estilos
            'sale_line_stock_warehouse/static/src/scss/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 1,
} 
