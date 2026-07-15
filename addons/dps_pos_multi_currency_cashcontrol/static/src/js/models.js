/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    
    async setup() {
        await super.setup(...arguments);
        let self = this;
        this.currencies = this.models["res.currency"].getAll();
        this.currencies_rate = {};
        this.currencies_symbol = {};
        this.currencies.forEach(curr => {
            this.currencies_rate[curr.name] = curr.rate;
            this.currencies_symbol[curr.name] = curr.symbol;
        });
    },
    
});