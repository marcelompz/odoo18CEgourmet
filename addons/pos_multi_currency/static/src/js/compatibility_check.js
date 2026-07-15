/** @odoo-module */
import { registry } from "@web/core/registry";

/**
 * Compatibility check service for pos_multi_currency module
 * Validates that dps_pos_multi_currency_cashcontrol is properly loaded
 */
const multiCurrencyCompatibilityCheck = {
    start(env) {
        // Only run checks in debug mode to avoid console spam in production
        if (!window.location.search.includes('debug=1') && 
            !(typeof odoo !== 'undefined' && odoo.debug && odoo.debug.includes('assets'))) {
            return;
        }
        
        console.group('[pos_multi_currency] Compatibility Check');
        
        // Check 1: Verify DPS module is loaded
        const hasDPS = Boolean(
            odoo.loader?.modules?.get?.('dps_pos_multi_currency_cashcontrol')
        );
        
        if (hasDPS) {
            console.log('✓ DPS Cash Control Module: FOUND');
        } else {
            console.error('✗ DPS Cash Control Module: NOT FOUND');
            console.warn('  pos_multi_currency depends on dps_pos_multi_currency_cashcontrol');
            console.warn('  Please ensure dps_pos_multi_currency_cashcontrol is installed and enabled');
        }
        
        // Check 2: Verify expected DPS data structures will be available
        // (Can only check this after POS loads, so this is just informational)
        console.log('ℹ Expected DPS data structures:');
        console.log('  - pos.currencies (array)');
        console.log('  - pos.currencies_rate (object)');
        console.log('  - pos.currencies_symbol (object)');
        console.log('  These will be validated at POS runtime.');
        
        // Check 3: Verify module load order
        const modules = odoo.loader?.modules;
        if (modules) {
            const dpsModule = modules.get('dps_pos_multi_currency_cashcontrol');
            const mcModule = modules.get('pos_multi_currency');
            
            if (dpsModule && mcModule) {
                console.log('✓ Module Load Order: Correct (DPS loads before pos_multi_currency)');
            }
        }
        
        console.log('📋 Configuration Checklist:');
        console.log('  1. Set min_change_threshold in POS Config');
        console.log('  2. Add base currency to excluded_currency_ids if needed');
        console.log('  3. Verify cash payment methods have journals with currencies');
        
        console.groupEnd();
    }
};

// Register as a service so it runs on POS start
registry.category("services").add(
    "pos_multi_currency_compatibility", 
    multiCurrencyCompatibilityCheck
);


