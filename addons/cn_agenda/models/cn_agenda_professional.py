# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class CnAgendaProfessional(models.Model):
    _name = 'cn.agenda.professional'
    _description = 'Professional'
    _rec_name = 'partner_id'
    
    partner_id = fields.Many2one('res.partner', string='Contact', required=True, ondelete='cascade', domain="[('is_company', '=', False)]")
    
    # Related fields to show contact info without storing it again
    name = fields.Char(related='partner_id.name', string='Name', readonly=True, store=True)
    email = fields.Char(related='partner_id.email', string='Email', readonly=True)
    phone = fields.Char(related='partner_id.phone', string='Phone', readonly=True)
    mobile = fields.Char(related='partner_id.mobile', string='Mobile', readonly=True)
    image_1920 = fields.Image(related='partner_id.image_1920', string="Image", readonly=True)

    specialty = fields.Char(string='Specialty')
    schedule_ids = fields.One2many('cn.agenda.professional.schedule', 'professional_id', string='Working Schedule')
    absence_ids = fields.One2many('cn.agenda.professional.absence', 'professional_id', string='Absences')
    
    _sql_constraints = [
        ('partner_uniq', 'unique (partner_id)', 'A contact can be linked to only one professional record!')
    ]

    def get_schedule_for_day(self, day_index):
        """Returns the working hours for a given day index (0=Monday, 6=Sunday)."""
        return self.schedule_ids.filtered(lambda s: s.day_of_week == str(day_index))

class CnAgendaProfessionalSchedule(models.Model):
    _name = 'cn.agenda.professional.schedule'
    _description = 'Professional Schedule'
    _order = 'day_of_week, hour_start'
    
    professional_id = fields.Many2one('cn.agenda.professional', string='Professional', required=True, ondelete='cascade')
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
    ], string='Day of Week', required=True)
    hour_start = fields.Float(string='Start Hour', required=True, help="Start time in military format (e.g., 9.5 for 09:30)")
    hour_end = fields.Float(string='End Hour', required=True, help="End time in military format (e.g., 17.0 for 17:00)")

    @api.constrains('hour_start', 'hour_end')
    def _check_validity(self):
        for record in self:
            if record.hour_start >= record.hour_end:
                raise models.ValidationError(_("Start hour must be before end hour."))

class CnAgendaProfessionalAbsence(models.Model):
    _name = 'cn.agenda.professional.absence'
    _description = 'Professional Absence'
    
    professional_id = fields.Many2one('cn.agenda.professional', string='Professional', required=True, ondelete='cascade')
    date_start = fields.Datetime(string='Start Date', required=True)
    date_end = fields.Datetime(string='End Date', required=True)
    reason = fields.Char(string='Reason')

    @api.constrains('date_start', 'date_end')
    def _check_validity(self):
        for record in self:
            if record.date_start >= record.date_end:
                raise models.ValidationError(_("Start date must be before end date."))
