# -*- coding: utf-8 -*-
{
    'name': "Stock Visibility & Restrictions for POS",
    'summary': 'Enhances POS by adding real-time product stock visibility and options to restrict or hide out-of-stock items.',
    'description': """
        This module enhances the Point of Sale (POS) system by adding two key features:
        
        - **Real-time Stock Visibility**: Displays the stock level for each product directly on the POS screen. The stock is updated dynamically as products are sold, providing instant insights into available quantities.
        
        - **Out-of-Stock Restrictions**: Adds two options to the POS settings that allow you to:
          - Restrict sales of out-of-stock products.
          - Hide out-of-stock products from the product list entirely.
        
        This module ensures that the POS system provides more efficient stock management and prevents errors associated with selling unavailable products. It’s especially useful for businesses with high inventory turnover or where stock levels are critical to sales accuracy.
    """,
    'author': "Shahid Khan",
    'website': "https://github.com/shahid-0",
    'category': 'Point of Sale',
    'version': '18.0.1.0.0',
    'depends': ["point_of_sale"],
    'data': [
        "views/res_config_setting_views.xml"
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_stock_visibility_restriction/static/src/**/*',
        ]
    },
    'images': ['static/description/banner.gif'],
    'demo': [],
    'license': 'LGPL-3',
}

