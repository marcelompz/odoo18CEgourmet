import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration script for pos_multi_currency compatibility changes
    Sets default values for new configuration fields
    """
    _logger.info("Running pos_multi_currency compatibility migration...")
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Set default threshold for all existing POS configs
    configs = env['pos.config'].search([])
    _logger.info(f"Found {len(configs)} POS configurations to update")
    
    for config in configs:
        try:
            # Set default min_change_threshold if not set
            if not config.min_change_threshold:
                config.min_change_threshold = 100.0
                _logger.info(f"Set min_change_threshold=100 for POS config: {config.name}")
            
            # Auto-exclude base currency if it matches company currency
            company_currency = config.company_id.currency_id
            if company_currency and company_currency not in config.excluded_currency_ids:
                # Check if this is likely the base currency (PYG in original code)
                if company_currency.name == 'PYG':
                    config.excluded_currency_ids = [(4, company_currency.id)]
                    _logger.info(f"Auto-excluded PYG from exchange rates for POS config: {config.name}")
            
        except Exception as e:
            _logger.error(f"Error migrating POS config {config.name}: {str(e)}")
            continue
    
    _logger.info("pos_multi_currency compatibility migration completed")
    _logger.info("=" * 70)
    _logger.info("IMPORTANT: Review POS Configuration settings")
    _logger.info("Location: Point of Sale > Configuration > Point of Sale")
    _logger.info("New fields in 'Multi-Currency Settings' section:")
    _logger.info("  - Minimum Change Threshold")
    _logger.info("  - Excluded Currencies from Display")
    _logger.info("=" * 70)


