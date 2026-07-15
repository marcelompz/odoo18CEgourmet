# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_hide_zero_stock = fields.Boolean(related = 'pos_config_id.hide_zero_stock', readonly=False)
    pos_restrict_zero_stock = fields.Boolean(related = 'pos_config_id.restrict_zero_stock', readonly=False)

