# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MassImportSuiteWizard(models.TransientModel):
    _name = 'mass.import.suite'
    _description = 'Mass Import Suite Launcher'

    def action_open_product_import(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.mass.import.wizard',
            'view_mode': 'form',
            'target': 'current',
            'context': dict(self.env.context, default_name='Nuevo'),
        }

    def action_open_recipe_import(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'excel.recipe.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context),
        }
