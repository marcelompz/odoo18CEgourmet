# -*- coding: utf-8 -*-
"""
Created on 2025-09-25 12:44:49

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CurrencyRateWarningWizard(models.TransientModel):
    _name = 'pos.currency.rate.warning.wizard'
    _description = 'Wizard de Alerta de Tasa de Cambio Faltante'

    missing_currencies_text = fields.Text(string="Monedas sin Tasa de Cambio", readonly=True)

    def action_open_currency_rates(self):
        """
        Devuelve una acción para abrir la vista de Tasas de Cambio.
        """
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_currency_form')
        # Podemos añadir un dominio para mostrar solo las de hoy, aunque no es necesario
        # action['domain'] = [('name', '=', fields.Date.context_today(self))]
        return action
