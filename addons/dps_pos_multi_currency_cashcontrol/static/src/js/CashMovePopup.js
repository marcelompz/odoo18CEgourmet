/** @odoo-module */

import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { useRef } from "@odoo/owl";
import { parseFloat } from "@web/views/fields/parsers";
import { CashMoveReceipt } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_receipt/cash_move_receipt";


patch(CashMovePopup.prototype, {
    setup() {
        super.setup();
        this.oc_select = useRef("oc_select");
        this.onSelectChange = this.onSelectChange.bind(this);
        this.other_currency = "";
    },

    onSelectChange() {
        if (this.oc_select.el) {
            const selectedValue = this.oc_select.el.value;
            this.other_currency = selectedValue;
        }
    },   

    async confirm() {
        let amount = parseFloat(this.state.amount);
        let oc_name = '';
        if (this.other_currency && this.other_currency != this.pos.currency.name) {
            let oc_rate = this.pos.currencies_rate[this.other_currency];
            amount = amount  / oc_rate;
            oc_name = this.other_currency;
        }
        const formattedAmount = this.env.utils.formatCurrency(amount);
        if (!amount) {
            this.notification.add(_t("Cash in/out of %s is ignored.", formattedAmount));
            return this.props.close();
        }

        const type = this.state.type;
        const translatedType = _t(type);
        const extras = { formattedAmount, translatedType, oc_name };
        const reason = this.state.reason.trim();

        await this.pos.data.call(
            "pos.session",
            "try_cash_in_out",
            this._prepare_try_cash_in_out_payload(type, amount, reason, extras),
            {},
            true
        );
        await this.pos.logEmployeeMessage(
            `${_t("Cash")} ${translatedType} - ${_t("Amount")}: ${formattedAmount}`,
            "CASH_DRAWER_ACTION"
        );
        await this.printer.print(CashMoveReceipt, {
            reason,
            translatedType,
            formattedAmount,
            headerData: this.pos.getReceiptHeaderData(),
            date: new Date().toLocaleString(),
        });

        this.props.close();
        this.notification.add(
            _t("Successfully made a cash %s of %s.", type, formattedAmount),
            3000
        );
    },
});