# -*- coding: utf-8 -*-
"""
Created on 2025-06-10 09:44:32

@author: drojo
"""
# python
import logging

# odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    in_invoice_stamped = fields.Char(
        string='Timbrado')

    @api.onchange('invoice_number')
    def _onchange_invoice_number(self):
        if self.invoice_number:
            # Quitar espacios y normalizar el valor
            raw_number = self.invoice_number.replace(" ", "")
            parts = raw_number.split("-")

            if len(parts) != 3:  # Si no tiene 3 partes, asumimos que es un numero que no necesita ser formateado
                return
            # Asegurar que cada parte tenga el formato esperado
            try:
                part1 = parts[0].zfill(3) if len(parts) > 0 else "000"
                part2 = parts[1].zfill(3) if len(parts) > 1 else "000"
                part3 = parts[2].zfill(7) if len(parts) > 2 else "0000000"

                # Actualizar el campo con el formato estándar
                self.invoice_number = f"{part1}-{part2}-{part3}"
            except IndexError:
                self.invoice_number = ""  # Limpia si hay un error en el formato 

    @api.onchange('in_invoice_stamped', 'invoice_number')
    def onchange_in_invoice_stamped(self):
        text_concatenated = ''

        if self.invoice_number:
            text_concatenated += self.invoice_number

        if self.in_invoice_stamped:
            if text_concatenated:
                text_concatenated += ' | '
            text_concatenated += f'Timbrado: {self.in_invoice_stamped}'

        self.ref = text_concatenated
    