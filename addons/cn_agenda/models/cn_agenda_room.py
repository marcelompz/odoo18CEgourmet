# -*- coding: utf-8 -*-

from odoo import models, fields

class CnAgendaRoom(models.Model):
    _name = 'cn.agenda.room'
    _description = 'Room/Resource'
    
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    capacity = fields.Integer(string='Capacity', default=1)
