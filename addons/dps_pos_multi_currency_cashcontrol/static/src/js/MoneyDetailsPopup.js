/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { MoneyDetailsPopup } from "@point_of_sale/app/utils/money_details_popup/money_details_popup";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
import { floatIsZero } from "@web/core/utils/numbers";

patch(MoneyDetailsPopup.prototype, {
    setup() {
        super.setup();
        
        // --- EXPORTAR FUNCIONES AL XML ---
        this.parseFloat = parseFloat;
        this.Object = Object;

        let bills = this.pos.models["pos.bill"].filter((bill) => !bill.currency_id);
        var initialState = {
            moneyDetails: Object.fromEntries(bills.map(bill => [bill.value, 0])),
        };

        let allBills = this.pos.models["pos.bill"].getAll();
        const grouped = allBills.reduce((acc, obj) => {
            if (obj.currency_id) {
                (acc[obj.currency_id.name] ??= []).push(obj);
            }
            return acc;
        }, {});

        this.otherCurrencies = Object.keys(grouped);
        this.otherCurrencies.forEach(key => {
            let mdKey = `moneyDetails${key}`;
            let mdVals = {};
            grouped[key].forEach(oc => {
                // Usamos el valor numérico como clave siempre
                if (oc.value != null) {
                    mdVals[oc.value] = 0; 
                }
            });
            initialState[mdKey] = mdVals;
        });

        this.state = useState(initialState);
        this.moneyDetailKeys = Object.keys(this.state).filter(k => k.startsWith("moneyDetails"));
    },

    _getCalculatedTotal(key) {
        if (!this.state[key]) return 0;
        return Object.entries(this.state[key]).reduce((acc, [val, qty]) => {
            const numQty = parseFloat(qty) || 0;
            const numVal = parseFloat(val) || 0;
            return acc + (numVal * numQty);
        }, 0);
    },

    computeTotalAllCurrencywithSymbol() {
        let results = [];
        const baseTotal = this._getCalculatedTotal('moneyDetails');
        results.push({ label: 'Total', value: this.env.utils.formatCurrency(baseTotal) });

        this.moneyDetailKeys.forEach(key => {
            let curr_key = key.replace('moneyDetails', '');
            if (curr_key) {
                const total = this._getCalculatedTotal(key);
                results.push({ 
                    label: `Total ${curr_key}`, 
                    value: `${this.env.utils.formatCurrency(total, false)} ${this.currency_symbol(curr_key)}`
                });
            }
        });
        return results;
    },

    computeTotalAllCurrency() {
        let curr_vals = {};
        curr_vals[`Total`] = this._getCalculatedTotal('moneyDetails');
        this.moneyDetailKeys.forEach(key => {
            let curr_key = key.replace('moneyDetails', '');
            if (curr_key) {
                curr_vals[`Total ${curr_key}`] = this._getCalculatedTotal(key);
            }
        });
        return curr_vals;
    },

    currency_symbol(curr_key) {
        return this.pos.currencies_symbol[curr_key] || this.pos.currency.symbol;
    },

    confirm() {
        let totalBase = this._getCalculatedTotal('moneyDetails');
        let moneyDetailsNotes = "details: \n";
        
        this.moneyDetailKeys.forEach(key => {
            const isBase = key === "moneyDetails";
            const currName = isBase ? "" : key.replace('moneyDetails', '');
            
            Object.entries(this.state[key]).forEach(([val, qty]) => {
                if (parseFloat(qty) > 0) {
                    const formattedVal = this.env.utils.formatCurrency(parseFloat(val), !currName);
                    moneyDetailsNotes += `\t ${qty} x ${formattedVal} ${isBase ? '' : this.currency_symbol(currName)}\n`;
                }
            });

            if (!isBase) {
                let rate = this.pos.currencies_rate[currName] || 1;
                totalBase += this._getCalculatedTotal(key) / rate;
            }
        });

        this.props.getPayload({
            total: totalBase,
            moneyDetailsNotes: moneyDetailsNotes + _t("Total: %s", this.env.utils.formatCurrency(totalBase)),
            moneyDetails: { ...this.state.moneyDetails },
            action: this.props.action,
            all_currency_total: this.computeTotalAllCurrency(),
        });
        this.props.close();
    },
});
