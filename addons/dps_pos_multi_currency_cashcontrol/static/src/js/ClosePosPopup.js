/** @odoo-module */

import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";

let new_props = ['oc_details']
let extended = [...ClosePosPopup.props, ...new_props];

patch(ClosePosPopup, {
    props: extended
});

patch(ClosePosPopup.prototype, {
    setup() {
        super.setup();
    },

    get cashMoveData() {
        const { total, moves } = this.props.default_cash_details.moves.reduce(
            (acc, move, i) => {
                acc.total += move.amount;
                acc.moves.push({
                    id: i,
                    name: move.name,
                    amount: move.amount,
                    other_curr : move.other_curr,
                    other_curr_amt : move.other_curr_amt,
                    other_curr_symbol : move.other_curr_symbol,

                });
                return acc;
            },
            { total: 0, moves: [] }
        );
        return { total, moves };
    },
});
