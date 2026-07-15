# -*- coding: utf-8 -*-
{
    'name': 'Prospecting & AI Demo Generator',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Prospect clients using Google Maps and generate Web Demos.',
    'author': 'Crossnexion E. A. S.',
    'website': 'https://www.crossnexion.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/prospecting_lead_views.xml',
        'views/prospecting_campaign_views.xml',
        'views/prospecting_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'description': """
Prospecting & AI Demo Generator
===============================
Identify businesses using Google Maps and generate tailored website proposals.

Features:
- Google Maps Search Integration.
- Website Technology Scraping (Simulated/Basic).
- One-Click HTML Landing Page Generator for prospects.

Generado por Crossnexion E. A. S. - Odoo v18 Architect.
    """,
}
