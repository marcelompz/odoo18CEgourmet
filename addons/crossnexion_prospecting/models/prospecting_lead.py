# -*- coding: utf-8 -*-
import logging
import base64
import random

# Try importing scraping libraries, handle if missing
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProspectingLead(models.Model):
    _name = 'prospecting.lead'
    _description = 'Prospecting Lead'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    campaign_id = fields.Many2one('prospecting.campaign', string='Campaign', ondelete='cascade')
    name = fields.Char(string='Business Name', required=True)
    
    # Google Data
    place_id = fields.Char(string='Google Place ID')
    address = fields.Char(string='Address')
    rating = fields.Float(string='Rating')
    user_ratings_total = fields.Integer(string='Review Count')
    
    # Contact Info
    website = fields.Char(string='Website')
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')
    
    # Scoring / Status
    has_website = fields.Boolean(string='Has Website', compute='_compute_has_website', store=True)
    tech_stack = fields.Text(string='Detected Tech', help="Technologies detected via scraping (e.g., WordPress, Odoo)")
    social_links = fields.Text(string='Social Links', help="Social Media URLs found")
    
    json_data = fields.Text(string='Raw JSON Data')
    
    demo_page_url = fields.Char(string='Demo Page URL', readonly=True)
    demo_html_content = fields.Html(string='Generated Demo Content')

    @api.depends('website')
    def _compute_has_website(self):
        for record in self:
            record.has_website = bool(record.website)

    def action_fetch_details(self):
        """
        Fetches more details (phone, website) using Place Details API 
        if not already present. Charges extra on Google API.
        """
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('crossnexion_prospecting.google_maps_api_key')
        if not api_key or not self.place_id:
            return

        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': self.place_id,
            'fields': 'name,website,formatted_phone_number,international_phone_number',
            'key': api_key
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            if data.get('status') == 'OK':
                result = data.get('result', {})
                self.write({
                    'website': result.get('website') or self.website,
                    'phone': result.get('formatted_phone_number') or self.phone,
                })
        except Exception as e:
            _logger.warning("Failed to fetch place details: %s", e)

    def action_scrape_website(self):
        """
        Scrapes the website to find basic tech info and social links.
        """
        self.ensure_one()
        if not self.website:
            raise UserError(_("No website URL to scrape."))
        
        if not requests or not BeautifulSoup:
            raise UserError(_("Python libraries 'requests' or 'beautifulsoup4' not installed."))

        try:
            # Add http if missing
            url = self.website if self.website.startswith('http') else 'http://' + self.website
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProspectingBot/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Basic tech detection
                techs = []
                html_text = response.text.lower()
                if 'wp-content' in html_text or 'wordpress' in html_text:
                    techs.append('WordPress')
                if 'odoo' in html_text:
                    techs.append('Odoo')
                if 'shopify' in html_text:
                    techs.append('Shopify')
                if 'wix' in html_text:
                    techs.append('Wix')
                
                # Social Links
                socials = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if any(x in href for x in ['facebook.com', 'instagram.com', 'linkedin.com', 'twitter.com']):
                        socials.append(href)
                
                self.write({
                    'tech_stack': ', '.join(techs) if techs else 'Unknown',
                    'social_links': '\n'.join(list(set(socials))),
                })
                self.message_post(body=_("Scraping completed."))
            else:
                self.message_post(body=_("Website unreachable. Status: %s") % response.status_code)

        except Exception as e:
            _logger.error("Scraping error: %s", e)
            self.message_post(body=_("Scraping failed: %s") % str(e))

    def action_generate_demo(self):
        """
        Generates a static HTML demo page tailored to the business.
        """
        self.ensure_one()
        
        # Simple template engine
        business_name = self.name or "Client"
        industry = self.campaign_id.keyword or "Service"
        
        # In a real app, this would use a robust QWeb template or Jinja2
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Proposal for {business_name}</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 0; background: #f8f9fa; }}
                header {{ background: #714B67; color: white; padding: 40px; text-align: center; }}
                h1 {{ margin: 0; font-size: 2.5rem; }}
                .container {{ max-width: 800px; margin: 40px auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .btn {{ display: inline-block; padding: 12px 24px; background: #00A09D; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; }}
                .features {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 40px; }}
                .feature {{ padding: 20px; border: 1px solid #eee; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <header>
                <h1>Website Upgrade for {business_name}</h1>
                <p>Maximize your potential in the {industry} industry.</p>
            </header>
            <div class="container">
                <h2>Why {business_name} needs a modern web presence?</h2>
                <p>We noticed you are doing great with a rating of {self.rating} stars! But your digital presence could use a boost to capture more customers.</p>
                
                <div class="features">
                    <div class="feature">
                        <h3>Online Reservations</h3>
                        <p>Allow customers to book directly from your site.</p>
                    </div>
                    <div class="feature">
                        <h3>Modern Design</h3>
                        <p>Mobile-responsive and fast loading.</p>
                    </div>
                </div>
                
                <br><br>
                <div style="text-align: center;">
                    <a href="#" class="btn">Get Started Now</a>
                </div>
            </div>
            <footer style="text-align: center; padding: 20px; color: #666;">
                Generated by Crossnexion for {business_name}
            </footer>
        </body>
        </html>
        """
        
        self.demo_html_content = html_template
        
        # Attach HTML file to the record
        attachment = self.env['ir.attachment'].create({
            'name': f"Demo_{business_name}.html",
            'type': 'binary',
            'datas': base64.b64encode(html_template.encode('utf-8')),
            'res_model': 'prospecting.lead',
            'res_id': self.id,
            'mimetype': 'text/html',
        })
        
        # Get URL for the attachment
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = f"{base_url}/web/content/{attachment.id}?download=true"
        
        self.demo_page_url = download_url
        
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'new',
        }

# Generado por Crossnexion E. A. S. - Odoo v18 Architect.
