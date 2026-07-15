/** @odoo-module */

import { OpeningControlPopup } from "@point_of_sale/app/store/opening_control_popup/opening_control_popup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { MoneyDetailsPopup } from "@point_of_sale/app/utils/money_details_popup/money_details_popup";
import { RPCError } from "@web/core/network/rpc";

patch(OpeningControlPopup.prototype, {
    setup() {
        super.setup(...arguments);
        this.usd_bal = 0;
		this.vef_bal = 0;
        this.all_currency_total = {};
    },

    async confirm() {
        try {
            await this.pos.data.call(
                "pos.session",
                "set_opening_control",
                [this.pos.session.id, parseFloat(this.state.openingCash), this.state.notes],
                {},
                true
            );
            if(this.all_currency_total){
                await this.pos.data.call(
                    "pos.session",
                    "set_other_currency_opening_bal",
                    [this.pos.session.id,this.all_currency_total],
                );
            }
        } catch (error) {
            if (
                error instanceof RPCError &&
                error.data.name === "odoo.exceptions.MissingError" &&
                (await this.pos.isSessionDeleted())
            ) {
                return window.location.reload();
            }
            throw error;
        }
        this.pos.session.state = "opened";
        this.props.close();
    },

    async openDetailsPopup() {
        const action = _t("Cash control - opening");
        this.hardwareProxy.openCashbox(action);
        this.dialog.add(MoneyDetailsPopup, {
            moneyDetails: this.moneyDetails,
            action: action,
            getPayload: (payload) => {
                if (payload) {
                    const { total, moneyDetails, moneyDetailsNotes } = payload;
                    this.state.openingCash = total;
                    if (moneyDetailsNotes) {
                        this.state.notes = moneyDetailsNotes;
                    }
                    this.moneyDetails = moneyDetails;
                    this.all_currency_total = payload.all_currency_total;
                }
            },
            context: "Opening",
        });
    },

});