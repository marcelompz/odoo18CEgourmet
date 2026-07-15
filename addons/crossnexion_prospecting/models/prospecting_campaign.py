# -*- coding: utf-8 -*-
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProspectingCampaign(models.Model):
    _name = 'prospecting.campaign'
    _description = 'Prospecting Campaign'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Campaign Name', required=True, tracking=True)
    location_query = fields.Char(
        string='Location/Area',
        required=True,
        help="E.g., 'New York', 'Paris', 'lat,lng'",
        default="New York"
    )
    keyword = fields.Char(
        string='Keyword/Category',
        required=True,
        help="E.g., 'Pizza', 'Gym', 'Web Agency'",
        default="Restaurant"
    )
    radius = fields.Integer(
        string='Radius (Meters)', 
        default=5000, 
        help="Radius for the search if using coordinates."
    )
    lead_ids = fields.One2many('prospecting.lead', 'campaign_id', string='Leads')
    lead_count = fields.Integer(compute='_compute_lead_count', string='Lead Count')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Searched'),
    ], default='draft', string='Status', tracking=True)

    @api.depends('lead_ids')
    def _compute_lead_count(self):
        for record in self:
            record.lead_count = len(record.lead_ids)

    def action_search_places(self):
        """
        Connects to Google Places API (Text Search) to find businesses.
        """
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('crossnexion_prospecting.google_maps_api_key')
        
        if not api_key:
            raise UserError(_("Please configure the Google Maps API Key in Settings."))

        # Google Places Text Search API endpoint
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        query = f"{self.keyword} in {self.location_query}"
        
        params = {
            'query': query,
            'key': api_key,
            'radius': self.radius,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') not in ['OK', 'ZERO_RESULTS']:
                raise UserError(_("Google API Error: %s") % data.get('error_message', data.get('status')))

            results = data.get('results', [])
            
            if not results:
                self.message_post(body=_("No results found for this query."))
                return

            Lead = self.env['prospecting.lead']
            created_count = 0
            
            for place in results:
                # Avoid duplicates in the same campaign based on Place ID
                existing = Lead.search([
                    ('place_id', '=', place.get('place_id')), 
                    ('campaign_id', '=', self.id)
                ], limit=1)
                
                if not existing:
                    Lead.create({
                        'campaign_id': self.id,
                        'name': place.get('name'),
                        'place_id': place.get('place_id'),
                        'address': place.get('formatted_address'),
                        'rating': place.get('rating'),
                        'user_ratings_total': place.get('user_ratings_total'),
                        'json_data': str(place),
                    })
                    created_count += 1
            
            self.state = 'done'
            self.message_post(body=_("Search completed. %s new leads found.") % created_count)

        except requests.exceptions.RequestException as e:
            _logger.error("Error connecting to Google Places API: %s", e)
            raise UserError(_("Network error while ensuring connection to Google Maps."))

        return True

    def action_view_leads(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Leads'),
            'res_model': 'prospecting.lead',
            'view_mode': 'tree,form',
            'domain': [('campaign_id', '=', self.id)],
            'context': {'default_campaign_id': self.id},
        }

# Generado por Crossnexion E. A. S. - Odoo v18 Architect.
