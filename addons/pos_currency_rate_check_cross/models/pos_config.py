# -*- coding: utf-8 -*-
"""
Created on 2025-09-25 12:47:30

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    def open_ui(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        company_currency_id = self.company_id.currency_id.id

        # 1. Buscamos todas las monedas activas EXCEPTO la de la compañía.
        #    La forma más segura es comparar IDs.
        currencies_to_check = self.env['res.currency'].search([
            ('active', '=', True),
            ('id', '!=', company_currency_id)
        ])

        if not currencies_to_check:
            # Si no hay otras monedas activas, no hay nada que comprobar.
            return super().open_ui()

        # 2. Buscamos las tasas para TODAS esas monedas en UNA SOLA consulta.
        #    Esto es mucho más eficiente que hacer un search_count dentro de un bucle.
        found_rates = self.env['res.currency.rate'].search([
            ('currency_id', 'in', currencies_to_check.ids),
            ('name', '=', today),
            ('company_id', '=', self.company_id.id),
        ])
        
        # 3. Obtenemos un set de las monedas para las que sí encontramos una tasa.
        currencies_with_rate = set(found_rates.mapped('currency_id.id'))

        # 4. Comparamos el set de monedas a comprobar con el set de monedas que tienen tasa.
        missing_rates_currencies = [
            currency.name for currency in currencies_to_check 
            if currency.id not in currencies_with_rate
        ]
        
        if missing_rates_currencies:
            wizard = self.env['pos.currency.rate.warning.wizard'].create({
                'missing_currencies_text': ", ".join(missing_rates_currencies)
            })
            return {
                'name': _('Faltan Tasas de Cambio'),
                'type': 'ir.actions.act_window',
                'res_model': 'pos.currency.rate.warning.wizard',
                'view_mode': 'form',
                'res_id': wizard.id,
                'target': 'new',
            }

        return super().open_ui()
