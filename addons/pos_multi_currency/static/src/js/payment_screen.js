/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

/**
 * Patch PaymentScreen to add currency display functionality
 *
 * Displays exchange rates and converted amounts for all cash payment method currencies.
 */

// Environment-aware debug flag (only enabled in development)
const DEBUG = window.location.hostname === 'localhost' || 
              window.location.search.includes('debug=1') ||
              (typeof odoo !== 'undefined' && odoo.debug && odoo.debug.includes('assets'));

const debugLog = (...args) => {
    if (DEBUG) {
        console.log('[pos_multi_currency]', ...args);
    }
};

patch(PaymentScreen.prototype, {
    setup() {
        debugLog('PaymentScreen setup() - START');
        super.setup();
        this.pos = usePos();
        this.state = useState({
            updateTrigger: 0,
            _exchangeRates: null,
            _dueAmounts: null,
            _changeAmounts: null
        });
        debugLog('PaymentScreen setup() - END, updateTrigger initialized:', this.state.updateTrigger);

        // Verify DPS module compatibility (defensive check)
        if (!this.pos.currencies_rate || !this.pos.currencies_symbol) {
            console.warn('[pos_multi_currency] DPS cash control currency data not found. Multi-currency display features may be limited.');
        }

        // Verify configuration
        if (!this.pos.config.cash_currency_ids || this.pos.config.cash_currency_ids.length === 0) {
            debugLog('[pos_multi_currency] No cash currencies configured. Using all available currencies from DPS.');
        }

        setTimeout(() => {
            debugLog('PaymentScreen Initializing amounts after setup');
            this.forceUpdateAmounts();
        }, 0);
    },

    forceUpdateAmounts() {
        debugLog('PaymentScreen forceUpdateAmounts() - START');
        const newExchangeRates = this._computeExchangeRates();
        const newDueAmounts = this._computeDueAmounts();
        const newChangeAmounts = this._computeChangeAmounts();

        debugLog('PaymentScreen forceUpdateAmounts() - Computed values:', {
            exchangeRates: newExchangeRates,
            dueAmounts: newDueAmounts,
            changeAmounts: newChangeAmounts
        });

        this.state._exchangeRates = newExchangeRates;
        this.state._dueAmounts = newDueAmounts;
        this.state._changeAmounts = newChangeAmounts;

        debugLog('PaymentScreen forceUpdateAmounts() - Updated state, new _dueAmounts:', this.state._dueAmounts);
    },

    async _isOrderValid(isForceValidate) {
        debugLog('PaymentScreen _isOrderValid() - Updating amounts');
        this.forceUpdateAmounts();
        return await super._isOrderValid(isForceValidate);
    },

    get currentOrder() {
        debugLog('PaymentScreen currentOrder getter - START');
        const order = this.pos.get_order();
        debugLog('PaymentScreen currentOrder getter - RETURN:', order);
        return order;
    },

    /**
     * Get only currencies that have bills configured in pos.bill
     */
    get cashCurrencies() {
        debugLog('PaymentScreen cashCurrencies getter - START (Filtered by pos.bill)');
        
        // 1. Obtener todos los IDs de monedas que tienen billetes configurados
        const bills = this.pos.models["pos.bill"].getAll();
        const billCurrencyIds = new Set(
            bills.filter(b => b.currency_id).map(b => b.currency_id.id)
        );

        // 2. Obtener la fuente de monedas (DPS o Config)
        let sourceCurrencies = [];
        if (this.pos.currencies && Array.isArray(this.pos.currencies)) {
            debugLog('PaymentScreen cashCurrencies - Using DPS currencies collection');
            sourceCurrencies = this.pos.currencies;
        } else if (this.pos.config.cash_currency_ids) {
            debugLog('PaymentScreen cashCurrencies - Using cash_currency_ids fallback');
            for (const {id: currencyId} of this.pos.config.cash_currency_ids) {
                const currency = this.pos.models['res.currency'].get(currencyId);
                if (currency) sourceCurrencies.push(currency);
            }
        }

        // 3. Filtrar: Solo devolver monedas que existan en la lista de billetes
        const filtered = sourceCurrencies.filter(curr => billCurrencyIds.has(curr.id));
        
        debugLog('PaymentScreen cashCurrencies - Filtered Currencies:', filtered.map(c => c.name));
        return filtered;
    },

    get baseCurrency() {
        debugLog('PaymentScreen baseCurrency getter - START');
        const currency = this.currentOrder?.currency_id || this.pos.currency;
        debugLog('PaymentScreen baseCurrency getter - RETURN:', currency);
        return currency;
    },

    convertAmount(amount, targetCurrency) {
        debugLog('PaymentScreen convertAmount() - START');
        debugLog('PaymentScreen convertAmount - amount:', amount, 'targetCurrency:', targetCurrency);

        if (!amount || !targetCurrency) {
            debugLog('PaymentScreen convertAmount() - RETURN: 0 (no amount or targetCurrency)');
            return 0;
        }

        const baseCurrency = this.baseCurrency;
        debugLog('PaymentScreen convertAmount - baseCurrency:', baseCurrency);

        // If same currency, no conversion needed
        if (baseCurrency.id === targetCurrency.id) {
            debugLog('PaymentScreen convertAmount() - RETURN:', amount, '(same currency)');
            return amount;
        }

        // Use DPS's rate lookup if available (faster than direct property access)
        const baseRate = this.pos.currencies_rate?.[baseCurrency.name] || baseCurrency.rate || 1;
        const targetRate = this.pos.currencies_rate?.[targetCurrency.name] || targetCurrency.rate || 1;
        
        debugLog('PaymentScreen convertAmount - baseRate:', baseRate, 'targetRate:', targetRate);

        const result = amount * (targetRate / baseRate);
        debugLog('PaymentScreen convertAmount() - RETURN:', result);
        return result;
    },

    formatCurrencyAmount(amount, currency) {
        debugLog('PaymentScreen formatCurrencyAmount() - START');
        debugLog('PaymentScreen formatCurrencyAmount - amount:', amount, 'currency:', currency);

        if (!currency) {
            debugLog('PaymentScreen formatCurrencyAmount() - RETURN: "" (no currency)');
            return '';
        }

        const decimals = currency.decimal_places !== undefined ? currency.decimal_places : 2;
        const roundedAmount = amount.toFixed(decimals);
        debugLog('PaymentScreen formatCurrencyAmount - decimals:', decimals, 'roundedAmount:', roundedAmount);

        let formattedNumber;
        if (decimals === 0) {
            const integerPart = roundedAmount.split('.')[0];
            formattedNumber = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        } else {
            const parts = roundedAmount.split('.');
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            formattedNumber = parts.join('.');
        }
        debugLog('PaymentScreen formatCurrencyAmount - formattedNumber:', formattedNumber);

        // Use DPS's symbol lookup if available (cached for performance)
        const symbol = this.pos.currencies_symbol?.[currency.name] || currency.symbol || currency.name;
        debugLog('PaymentScreen formatCurrencyAmount - symbol:', symbol, 'position:', currency.position);

        let result;
        if (currency.position === 'before') {
            result = `${symbol} ${formattedNumber}`;
        } else {
            result = `${formattedNumber} ${symbol}`;
        }
        debugLog('PaymentScreen formatCurrencyAmount() - RETURN:', result);
        return result;
    },

    _computeExchangeRates() {
        debugLog('PaymentScreen _computeExchangeRates - START');
        const baseCurrency = this.baseCurrency;
        debugLog('PaymentScreen _computeExchangeRates - baseCurrency:', baseCurrency);
        const rates = [];
        
        // Get excluded currency IDs from configuration (replaces hard-coded 'PYG' check)
        const excludedIds = this.pos.config.excluded_currency_ids || [];
        const excludedIdSet = new Set(excludedIds.map(c => c.id || c));

        for (const currency of this.cashCurrencies) {
            debugLog('PaymentScreen _computeExchangeRates - Processing currency:', currency);

            // Skip if currency is in the excluded list (configured in POS settings)
            if (!currency || excludedIdSet.has(currency.id)) {
                debugLog('PaymentScreen _computeExchangeRates - Skipping excluded currency:', currency?.name);
                continue;
            }

            const baseRate = baseCurrency?.rate || 1;
            const targetRate = currency.rate || 0;

            if (!targetRate) {
                debugLog('PaymentScreen _computeExchangeRates - Skipping due to missing targetRate');
                continue;
            }

            const rateValue = baseRate / targetRate;

            const rateItem = {
                id: currency.id,
                display: `1 ${currency.name} = ${this.formatCurrencyAmount(rateValue, baseCurrency)}`,
                currencyName: currency.name,
                rate: rateValue
            };
            debugLog('PaymentScreen _computeExchangeRates - Adding rate item:', rateItem);
            rates.push(rateItem);
        }

        debugLog('PaymentScreen _computeExchangeRates - RETURN:', rates);
        return rates;
    },

    get exchangeRates() {
        return this.state._exchangeRates || [];
    },

    _computeDueAmounts() {
        debugLog('PaymentScreen _computeDueAmounts - START');
        debugLog('PaymentScreen _computeDueAmounts - currentOrder:', this.currentOrder);

        if (!this.currentOrder) {
            debugLog('PaymentScreen _computeDueAmounts - RETURN: [] (no currentOrder)');
            return [];
        }

        const rawDueInBase = this.currentOrder.get_due();
        const dueInBase = Math.max(rawDueInBase, 0);
        debugLog('PaymentScreen _computeDueAmounts - rawDueInBase:', rawDueInBase, 'clamped dueInBase:', dueInBase);

        const amounts = [];
        //debugLog('this.cashCurrencies', this.cashCurrencies);
        for (const currency of this.cashCurrencies) {
            debugLog('PaymentScreen _computeDueAmounts - Processing currency:', currency);
            const convertedAmount = this.convertAmount(dueInBase, currency);

            const amountItem = {
                currencyId: currency.id,
                currencyName: currency.name,
                display: this.formatCurrencyAmount(convertedAmount, currency),
                amount: convertedAmount
            };
            debugLog('PaymentScreen _computeDueAmounts - Adding amount item:', amountItem);
            amounts.push(amountItem);
        }

        debugLog('PaymentScreen _computeDueAmounts - RETURN:', amounts);
        return amounts;
    },

    get dueAmounts() {
        return this.state._dueAmounts || [];
    },

    _computeChangeAmounts() {
        debugLog('PaymentScreen _computeChangeAmounts - START');
        debugLog('PaymentScreen _computeChangeAmounts - currentOrder:', this.currentOrder);

        if (!this.currentOrder) {
            debugLog('PaymentScreen _computeChangeAmounts - RETURN: null (no currentOrder)');
            return null;
        }

        const changeInBase = this.currentOrder.get_change();
        debugLog('PaymentScreen _computeChangeAmounts - changeInBase:', changeInBase);

        if (changeInBase <= 0) {
            debugLog('PaymentScreen _computeChangeAmounts - RETURN: null (changeInBase <= 0)');
            return null;
        }

        // Use configured threshold instead of hard-coded 100
        const threshold = this.pos.config.min_change_threshold || 0;
        if (threshold > 0 && changeInBase < threshold && changeInBase >= 0) {
            debugLog('PaymentScreen _computeChangeAmounts - RETURN: null (below configured threshold:', threshold, ')');
            return null;
        }

        const amounts = [];

        for (const currency of this.cashCurrencies) {
            debugLog('PaymentScreen _computeChangeAmounts - Processing currency:', currency);
            const convertedAmount = this.convertAmount(changeInBase, currency);

            const changeItem = {
                currencyId: currency.id,
                currencyName: currency.name,
                display: this.formatCurrencyAmount(convertedAmount, currency),
                amount: convertedAmount
            };
            debugLog('PaymentScreen _computeChangeAmounts - Adding change item:', changeItem);
            amounts.push(changeItem);
        }

        debugLog('PaymentScreen _computeChangeAmounts - RETURN:', amounts);
        return amounts;
    },

    get changeAmounts() {
        return this.state._changeAmounts;
    },

    selectPaymentLine(uuid) {
        debugLog('[PaymentScreen PATCH] selectPaymentLine() - CALLED WITH uuid:', uuid);
        const line = this.paymentLines.find((line) => line.uuid === uuid);
        this.currentOrder.select_paymentline(line);

        if (line && line.amount > 0) {
            const targetCurrency = line.get_target_currency();
            const config = this.pos.config;
            const baseCurrency = config.currency_id;

            if (targetCurrency && targetCurrency.id !== baseCurrency.id) {
                const amountInTarget = line.convert_from_base_to_target(line.amount);
                this.numberBuffer.set(amountInTarget.toFixed(targetCurrency.decimal_places || 2));
                debugLog('[PaymentScreen PATCH] selectPaymentLine() - Set numberBuffer to target currency amount:', {
                    amountInBase: line.amount,
                    amountInTarget: amountInTarget,
                    targetCurrency: targetCurrency.name
                });
            } else {
                this.numberBuffer.reset();
            }
        } else {
            this.numberBuffer.reset();
        }
    },

    async addNewPaymentLine(paymentMethod) {
        debugLog('PaymentScreen addNewPaymentLine() - START (OVERRIDE)');

        if (
            paymentMethod.type === "pay_later" &&
            (!this.currentOrder.to_invoice ||
                this.pos.models["ir.module.module"].find((m) => m.name === "pos_settle_due")
                    ?.state !== "installed")
        ) {
            this.notification.add(
                _t(
                    "To ensure due balance follow-up, generate an invoice or download the accounting application. "
                ),
                { autocloseDelay: 7000, title: _t("Warning") }
            );
        }

        if (this.pos.paymentTerminalInProgress && paymentMethod.use_payment_terminal) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("There is already an electronic payment in progress."),
            });
            return;
        }

        const dueInBase = this.currentOrder.get_due();

        const result = this.currentOrder.add_paymentline(paymentMethod);

        if (!this.check_cash_rounding_has_been_well_applied()) {
            return;
        }

        if (result) {
            const newPaymentLine = this.paymentLines.at(-1);

            if (newPaymentLine) {
                const targetCurrency = newPaymentLine.get_target_currency();
                const baseCurrency = this.pos.config.currency_id;

                if (targetCurrency && baseCurrency && targetCurrency.id !== baseCurrency.id) {
                    const dueInTarget = newPaymentLine.convert_from_base_to_target(dueInBase);

                    debugLog('PaymentScreen addNewPaymentLine() - Multi-currency adjustment:', {
                        dueInBase: dueInBase,
                        dueInTarget: dueInTarget,
                        baseCurrency: baseCurrency.name,
                        targetCurrency: targetCurrency.name
                    });

                    newPaymentLine.set_amount(dueInTarget);
                    this.numberBuffer.set(dueInTarget.toFixed(targetCurrency.decimal_places || 2));
                } else {
                    this.numberBuffer.reset();
                }
            } else {
                this.numberBuffer.reset();
            }

            if (
                paymentMethod.use_payment_terminal &&
                (paymentMethod.payment_terminal?.fast_payments ?? true)
            ) {
                const newPaymentLine = this.paymentLines.at(-1);
                this.sendPaymentRequest(newPaymentLine);
            }

            setTimeout(() => {
                debugLog('PaymentScreen addNewPaymentLine() - Updating amounts after tick');
                this.forceUpdateAmounts();
            }, 300);

            return true;
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("There is already an electronic payment in progress."),
            });
            return false;
        }
    },

    updateSelectedPaymentline(amount = false) {
        debugLog('[PaymentScreen PATCH] updateSelectedPaymentline() - CALLED WITH amount:', amount);

        const selectedLine = this.currentOrder.get_selected_paymentline();

        if (!selectedLine) {
            super.updateSelectedPaymentline(amount);
            this.forceUpdateAmounts();
            return;
        }

        if (this.paymentLines.every((line) => line.paid)) {
            this.currentOrder.add_paymentline(this.payment_methods_from_config[0]);
        }

        if (amount === false) {
            if (this.numberBuffer.get() === null) {
                amount = null;
            } else if (this.numberBuffer.get() === "") {
                amount = 0;
            } else {
                amount = this.numberBuffer.getFloat();
            }
        }

        const payment_terminal = selectedLine.payment_method_id.payment_terminal;
        const hasCashPaymentMethod = this.payment_methods_from_config.some(
            (method) => method.type === "cash"
        );

        const targetCurrency = selectedLine.get_target_currency();
        const config = this.pos.config;
        const baseCurrency = config.currency_id;
        const isMultiCurrency = targetCurrency && targetCurrency.id !== baseCurrency.id;

        debugLog('[PaymentScreen PATCH] Multi-currency context:', {
            isMultiCurrency: isMultiCurrency,
            targetCurrency: targetCurrency?.name,
            baseCurrency: baseCurrency.name,
            inputAmount: amount
        });

        let dueInTargetCurrency = this.currentOrder.get_due();
        if (isMultiCurrency && selectedLine) {
            dueInTargetCurrency = selectedLine.convert_from_base_to_target(this.currentOrder.get_due());
        }

        if (
            !hasCashPaymentMethod &&
            isMultiCurrency &&
            amount > dueInTargetCurrency + selectedLine.convert_from_base_to_target(selectedLine.amount)
        ) {
            selectedLine.set_amount(0);
            this.numberBuffer.set(dueInTargetCurrency.toFixed(targetCurrency.decimal_places || 2));
            amount = dueInTargetCurrency;
            this.showMaxValueError();
        } else if (
            !hasCashPaymentMethod &&
            !isMultiCurrency &&
            amount > this.currentOrder.get_due() + selectedLine.amount
        ) {
            selectedLine.set_amount(0);
            this.numberBuffer.set(this.currentOrder.get_due().toString());
            amount = this.currentOrder.get_due();
            this.showMaxValueError();
        }

        if (
            payment_terminal &&
            !["pending", "retry"].includes(selectedLine.get_payment_status())
        ) {
            this.forceUpdateAmounts();
            return;
        }

        if (amount === null) {
            this.deletePaymentLine(selectedLine.uuid);
        } else {
            selectedLine.set_amount(amount);
        }

        setTimeout(() => {
            debugLog('[PaymentScreen PATCH] updateSelectedPaymentline() - Updating amounts after tick');
            this.forceUpdateAmounts();
        }, 300);
    },

    deletePaymentLine(uuid) {
        debugLog('PaymentScreen deletePaymentLine() - START (OVERRIDE)');
        super.deletePaymentLine(uuid);
        // Force update amounts in state to trigger UI re-render
        // Use setTimeout to ensure order totals are recalculated first
        setTimeout(() => {
            debugLog('PaymentScreen deletePaymentLine() - Updating amounts after tick');
            this.forceUpdateAmounts();
        }, 300);
    }
});
