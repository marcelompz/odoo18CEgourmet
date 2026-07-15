/** @odoo-module */

import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { patch } from "@web/core/utils/patch";
import { roundDecimals } from "@web/core/utils/numbers";

patch(PosPayment.prototype, {
    get_target_currency() {
        const config = this.records['pos.config'].entries().next().value[1];

        if (!config) {
            return null;
        }

        const baseCurrency = config.currency_id;
        const paymentMethod = this.payment_method_id;

        if (!paymentMethod || !paymentMethod.journal_id) {
            return baseCurrency;
        }

        const journalId = typeof paymentMethod.journal_id === 'object' ? paymentMethod.journal_id.id : paymentMethod.journal_id;
        const journal = this.records['account.journal'].get(journalId);

        if (!journal || !journal.currency_id) {
            return baseCurrency;
        }

        const currencyId = typeof journal.currency_id === 'object' ? journal.currency_id.id : journal.currency_id;
        const targetCurrency = this.records['res.currency'].get(currencyId);

        return targetCurrency || baseCurrency;
    },

    convert_from_target_to_base(amountInTarget) {
        const config = this.records['pos.config'].entries().next().value[1];
        if (!config) {
            return amountInTarget;
        }

        const baseCurrency = config.currency_id;
        const targetCurrency = this.get_target_currency();

        if (!targetCurrency || baseCurrency.id === targetCurrency.id) {
            return amountInTarget;
        }

        // Try to use DPS's rate cache first (optimization)
        const posStore = config.pos || config;
        let baseRate, targetRate;

        if (posStore.currencies_rate) {
            baseRate = posStore.currencies_rate[baseCurrency.name] || baseCurrency.rate || 1;
            targetRate = posStore.currencies_rate[targetCurrency.name] || targetCurrency.rate || 1;
        } else {
            baseRate = baseCurrency.rate || 1;
            targetRate = targetCurrency.rate || 1;
        }

        const amountInBase = amountInTarget * (baseRate / targetRate);

        console.log('convert_from_target_to_base:', {
            amountInTarget: amountInTarget,
            targetCurrency: targetCurrency.name,
            baseCurrency: baseCurrency.name,
            baseRate: baseRate,
            targetRate: targetRate,
            amountInBase: amountInBase,
            usedDPSCache: !!posStore.currencies_rate
        });

        return amountInBase;
    },

    convert_from_base_to_target(amountInBase) {
        const config = this.records['pos.config'].entries().next().value[1];
        if (!config) {
            return amountInBase;
        }

        const baseCurrency = config.currency_id;
        const targetCurrency = this.get_target_currency();

        if (!targetCurrency || baseCurrency.id === targetCurrency.id) {
            return amountInBase;
        }

        // Try to use DPS's rate cache first (optimization)
        const posStore = config.pos || config;
        let baseRate, targetRate;

        if (posStore.currencies_rate) {
            baseRate = posStore.currencies_rate[baseCurrency.name] || baseCurrency.rate || 1;
            targetRate = posStore.currencies_rate[targetCurrency.name] || targetCurrency.rate || 1;
        } else {
            baseRate = baseCurrency.rate || 1;
            targetRate = targetCurrency.rate || 1;
        }

        const amountInTarget = amountInBase * (targetRate / baseRate);

        return amountInTarget;
    },

    set_amount(value) {
        //const config = this.records['pos.config'].get(1);
        //const order = config.records['pos.order'].get('pos.order_1');
        //console.log('records', config.records['pos.order'].get('pos.order_1').access_token);

        this.pos_order_id.assert_editable();

        const targetCurrency = this.get_target_currency();
        const config = this.records['pos.config'].entries().next().value[1];
        const baseCurrency = config?.currency_id;

        let amountToStore;
        let amountConverted;
        let conversionRate;
        let paymentCurrencyId;

        if (targetCurrency && baseCurrency && targetCurrency.id !== baseCurrency.id) {
            const valueInTarget = parseFloat(value) || 0;
            amountToStore = this.convert_from_target_to_base(valueInTarget);
            amountConverted = valueInTarget;

            const baseRate = baseCurrency.rate || 1;
            const targetRate = targetCurrency.rate || 1;
            conversionRate = targetRate / baseRate;
            paymentCurrencyId = targetCurrency.id;

            console.log('set_amount - Multi-currency conversion:', {
                inputValue: value,
                valueInTarget: valueInTarget,
                targetCurrency: targetCurrency.name,
                amountToStore: amountToStore,
                baseCurrency: baseCurrency.name,
                conversionRate: conversionRate
            });
        } else {
            amountToStore = parseFloat(value) || 0;
            amountConverted = amountToStore;
            conversionRate = 1.0;
            paymentCurrencyId = baseCurrency?.id;
        }

        this.update({
            amount: roundDecimals(
                amountToStore,
                this.pos_order_id.currency.decimal_places
            ),
            amount_converted: amountConverted,
            payment_currency_id: paymentCurrencyId,
            conversion_rate: conversionRate,
        });
    },

    get_amount() {
        return this.amount || 0;
    },

    get_converted_amount() {
        const config = this.records['pos.config'].entries().next().value[1];

        if (!config || !this.amount) {
            return 0;
        }

        const baseCurrency = config.currency_id;

        const paymentMethod = this.payment_method_id;
        if (!paymentMethod || !paymentMethod.journal_id) {
            return this.amount;
        }

        const journalId = typeof paymentMethod.journal_id === 'object' ? paymentMethod.journal_id.id : paymentMethod.journal_id;
        const journal = this.records['account.journal'].get(journalId);
        if (!journal) {
            return this.amount;
        }

        let targetCurrency;
        if (journal.currency_id) {
            const currencyId = typeof journal.currency_id === 'object' ? journal.currency_id.id : journal.currency_id;
            targetCurrency = this.records['res.currency'].get(currencyId);
        } else {
            targetCurrency = baseCurrency;
        }

        if (!targetCurrency || baseCurrency.id === targetCurrency.id) {
            return this.amount;
        }

        const baseRate = baseCurrency.rate || 1;
        const targetRate = targetCurrency.rate || 1;
        const convertedAmount = this.amount * (targetRate / baseRate);

        console.log('get_converted_amount:', {
            amount: this.amount,
            baseCurrency: baseCurrency.name,
            targetCurrency: targetCurrency.name,
            baseRate: baseRate,
            targetRate: targetRate,
            convertedAmount: convertedAmount
        });

        return convertedAmount;
    },

    get_converted_amount_display() {
        const config = this.records['pos.config'].entries().next().value[1];

        if (!config) {
            return this.formatCurrency(0, config?.currency_id);
        }

        const baseCurrency = config.currency_id;
        const paymentMethod = this.payment_method_id;

        if (!paymentMethod || !paymentMethod.journal_id) {
            return this.formatCurrency(this.amount || 0, baseCurrency);
        }

        const journalId = typeof paymentMethod.journal_id === 'object' ? paymentMethod.journal_id.id : paymentMethod.journal_id;
        const journal = this.records['account.journal'].get(journalId);

        if (!journal) {
            return this.formatCurrency(this.amount || 0, baseCurrency);
        }

        let targetCurrency;
        if (journal.currency_id) {
            const currencyId = typeof journal.currency_id === 'object' ? journal.currency_id.id : journal.currency_id;
            targetCurrency = this.records['res.currency'].get(currencyId);
        } else {
            targetCurrency = baseCurrency;
        }

        if (!targetCurrency || baseCurrency.id === targetCurrency.id) {
            return this.formatCurrency(this.amount || 0, baseCurrency);
        }

        const baseRate = baseCurrency.rate || 1;
        const targetRate = targetCurrency.rate || 1;
        const convertedAmount = (this.amount || 0) * (targetRate / baseRate);

        return this.formatCurrency(convertedAmount, targetCurrency);
    },

    formatCurrency(amount, currency) {
        if (!currency) {
            return amount.toFixed(2);
        }

        const decimals = currency.decimal_places !== undefined ? currency.decimal_places : 2;
        const roundedAmount = amount.toFixed(decimals);

        let formattedNumber;
        if (decimals === 0) {
            const integerPart = roundedAmount.split('.')[0];
            formattedNumber = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        } else {
            const parts = roundedAmount.split('.');
            parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            formattedNumber = parts.join('.');
        }

        const symbol = currency.symbol || currency.name;

        if (currency.position === 'before') {
            return `${symbol} ${formattedNumber}`;
        } else {
            return `${formattedNumber} ${symbol}`;
        }
    }
});
