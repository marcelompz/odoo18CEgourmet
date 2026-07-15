# -*- coding: utf-8 -*-
{
    "name": "POS Central Cashier",
    "summary": "Flujo Mostrador -> Caja para órdenes pendientes en POS",
    "version": "18.0.1.5.0",
    "category": "Point of Sale",
    "author": "Crossnexion E. A. S.",
    "license": "OPL-1",
    "depends": ["point_of_sale"],
    "data": [
        "data/sequence.xml",
        "views/pos_config_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_central_cashier/static/src/js/pos_central_cashier_patch.js",
            "pos_central_cashier/static/src/js/receipt_patch.js",
            "pos_central_cashier/static/src/js/custom_pos_screens.js",
            "pos_central_cashier/static/src/js/payment_screen_inherit.js",
            "pos_central_cashier/static/src/xml/custom_pos_templates.xml",
            "pos_central_cashier/static/src/xml/pos_ticket_inherit.xml",
        ],
    },
    "installable": True,
    "application": False,
}