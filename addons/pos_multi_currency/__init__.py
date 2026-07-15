from . import models

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Post-installation hook to log module initialization"""
    _logger.info("=" * 60)
    _logger.info("POS Multi Currency module installed successfully")
    _logger.info("This module depends on: dps_pos_multi_currency_cashcontrol")
    _logger.info("Configuration required:")
    _logger.info("  1. Point of Sale > Configuration > Point of Sale")
    _logger.info("  2. Set 'Minimum Change Threshold' (default: 100)")
    _logger.info("  3. Add currencies to 'Excluded Currencies' if needed")
    _logger.info("=" * 60)
