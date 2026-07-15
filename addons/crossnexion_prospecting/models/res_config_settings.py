# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_maps_api_key = fields.Char(
        string="Google Maps API Key",
        config_parameter='crossnexion_prospecting.google_maps_api_key',
        help="API Key for Google Places API."
    )
