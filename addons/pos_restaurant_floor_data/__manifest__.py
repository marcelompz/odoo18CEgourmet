# -*- coding: utf-8 -*-
{
    'name': 'POS Restaurant Floor & Table Backup / Seed Data',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Módulo de datos iniciales para Pisos y Mesas del PDV Restaurante',
    'description': """
Módulo de Datos Seed de Pisos y Mesas para Provecchio Gourmet / POS Restaurant.
Carga automáticamente los pisos (Barra, Jardín, Restó, Terraza) y sus respectivas mesas con sus coordenadas y dimensiones.
    """,
    'author': 'Crossnexion',
    'website': 'https://provecchio.com',
    'license': 'OPL-1',
    'depends': ['pos_restaurant'],
    'data': [
        'data/restaurant_floor_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
