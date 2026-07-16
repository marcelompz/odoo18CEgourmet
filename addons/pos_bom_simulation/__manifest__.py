# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP & Developer.
# © 2026.

{
    'name': 'POS & MRP BoM Simulation',
    'version': '18.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Interactive testing and simulation for POS BOM and MRP BoMs from the UI',
    'description': """
This module provides an interactive test/simulation runner in the Odoo user interface.
It allows testing the inventory consumption and accounting flows for both pos_product_bom and mrp modules.
You can run the simulation, inspect the created records, and analyze the resulting changes before/after processes.
    """,
    'author': 'Developer',
    'depends': [
        'point_of_sale',
        'mrp',
        'pos_product_bom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_bom_simulation_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
