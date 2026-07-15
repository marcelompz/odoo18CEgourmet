# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class CnAgendaAppointment(models.Model):
    _name = 'cn.agenda.appointment'
    _description = 'Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Patient/Client', required=True, tracking=True)
    professional_id = fields.Many2one('cn.agenda.professional', string='Professional', required=True, tracking=True)
    room_id = fields.Many2one('cn.agenda.room', string='Room/Resource', required=True, tracking=True)
    
    start_datetime = fields.Datetime(string='Start', required=True, tracking=True)
    stop_datetime = fields.Datetime(string='End', required=True, tracking=True)
    duration = fields.Float(string='Duration (Hours)', compute='_compute_duration', store=True, readonly=False)
    
    service_type = fields.Char(string='Service Type/Reason')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    google_event_id = fields.Char(string='Google Event ID', copy=False)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('cn.agenda.appointment') or _('New')
        return super().create(vals)

    @api.depends('start_datetime', 'stop_datetime')
    def _compute_duration(self):
        for record in self:
            if record.start_datetime and record.stop_datetime:
                duration = (record.stop_datetime - record.start_datetime).total_seconds() / 3600
                record.duration = duration
            else:
                record.duration = 0.0

    @api.onchange('start_datetime', 'duration')
    def _onchange_duration(self):
        if self.start_datetime and self.duration:
            self.stop_datetime = self.start_datetime + timedelta(hours=self.duration)

    @api.constrains('start_datetime', 'stop_datetime', 'professional_id', 'room_id')
    def _check_availability(self):
        for record in self:
            if record.state == 'cancel':
                continue
            
            if record.start_datetime >= record.stop_datetime:
                raise ValidationError(_("Start time must be before end time."))

            # 1. Check Professional Overlap
            overlaps = self.search([
                ('id', '!=', record.id),
                ('professional_id', '=', record.professional_id.id),
                ('state', '!=', 'cancel'),
                ('start_datetime', '<', record.stop_datetime),
                ('stop_datetime', '>', record.start_datetime),
            ])
            if overlaps:
                raise ValidationError(_("Professional is overlap with another appointment: %s") % overlaps[0].name)

            # 2. Check Room Overlap
            room_overlaps = self.search([
                ('id', '!=', record.id),
                ('room_id', '=', record.room_id.id),
                ('state', '!=', 'cancel'),
                ('start_datetime', '<', record.stop_datetime),
                ('stop_datetime', '>', record.start_datetime),
            ])
            if room_overlaps:
                raise ValidationError(_("Room is occupied by another appointment: %s") % room_overlaps[0].name)

            # 3. Check Professional Absences
            absences = self.env['cn.agenda.professional.absence'].search([
                ('professional_id', '=', record.professional_id.id),
                ('date_start', '<', record.stop_datetime),
                ('date_end', '>', record.start_datetime),
            ])
            if absences:
                raise ValidationError(_("Professional is absent during this time: %s") % absences[0].reason)

            # 4. Check Professional Schedule
            # Convert UTC datetime to user's timezone or company timezone?
            # Schedules are typically defined in float hours (0-24). 
            # We must convert appointment Datetime (UTC) to the professional's timezone.
            # For simplicity, assuming company timezone or UTC for now, but in real world this needs pytz.
            # Using self.env.user.tz for conversion to compare with float hours.
            
            user_tz = self.env.user.tz or 'UTC'
            import pytz
            local_tz = pytz.timezone(user_tz)
            
            start_dt_local = pytz.utc.localize(record.start_datetime).astimezone(local_tz)
            end_dt_local = pytz.utc.localize(record.stop_datetime).astimezone(local_tz)
            
            # Day of week: 0=Monday, 6=Sunday
            day_of_week = str(start_dt_local.weekday())
            
            # Fetch schedule for that day
            day_schedules = record.professional_id.get_schedule_for_day(day_of_week)
            
            if not day_schedules:
                # If no schedule defined for that day, assume NOT WORKING? Or working 24/7?
                # Usually implies not working.
                raise ValidationError(_("Professional does not work on this day."))
            
            # Check if appointment fits fully within ANY of the schedule slots
            # Example: 08:00-12:00, 14:00-18:00. Appt: 10:00-11:00 (OK). Appt: 11:30-12:30 (Fail).
            
            start_float = start_dt_local.hour + start_dt_local.minute / 60.0
            end_float = end_dt_local.hour + end_dt_local.minute / 60.0
            
            valid_slot = False
            for slot in day_schedules:
                if start_float >= slot.hour_start and end_float <= slot.hour_end:
                    valid_slot = True
                    break
            
            if not valid_slot:
                raise ValidationError(_("Appointment is outside of professional's working hours."))
            
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})
