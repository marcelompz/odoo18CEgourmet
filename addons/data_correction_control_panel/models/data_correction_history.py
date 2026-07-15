# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DataCorrectionHistory(models.Model):
    _name = 'data.correction.history'
    _description = 'Historial de Corrección de Datos e Impuestos'

    fecha_correccion = fields.Datetime(string='Fecha de Corrección', default=lambda self: fields.Datetime.now())
    usuario_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    tipo_correccion = fields.Char(string='Tipo de Corrección')
    tabla_afectada = fields.Selection([
        ('purchase', 'Compras'),
        ('pos', 'Ventas PdV'),
        ('sale', 'Ventas Módulo'),
        ('inventory', 'Inventario')
    ], string='Tabla Afectada')
    id_registro_afectado = fields.Integer(string='ID de Registro Afectado')
    campo_modificado = fields.Char(string='Campo Modificado')
    valor_anterior = fields.Char(string='Valor Anterior')
    valor_nuevo = fields.Char(string='Valor Nuevo')

    def action_undo(self):
        # Lógica para deshacer la corrección ("Revertir")
        # Esto requerirá implementación específica dependiendo del tipo y tabla
        pass
