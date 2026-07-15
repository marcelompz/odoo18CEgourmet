/** @odoo-module **/

import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";

patch(PartnerList.prototype, {
    setup() {
        super.setup(...arguments);
        onWillStart(async () => {
            const partners = this.pos.models["res.partner"].getAll();
            if (partners.length > 0) {
                const partnerIds = partners.map(p => p.id);
                try {
                    // Odoo 18 PoS uses "pos_data" service, accessible via this.pos.data
                    // We use execute with 'read' type to fetch the most recent data from the server
                    const result = await this.pos.data.execute({
                        type: 'read',
                        model: 'res.partner',
                        ids: partnerIds,
                        fields: ['outstanding_debt']
                    });

                    if (result && Array.isArray(result)) {
                        for (const row of result) {
                            const partner = this.pos.models["res.partner"].get(row.id);
                            if (partner) {
                                // Update the reactive record in the PoS store
                                partner.outstanding_debt = row.outstanding_debt;
                            }
                        }
                    }
                } catch (e) {
                    console.error("Error refreshing customer balances:", e);
                }
            }
        });
    },
    get isBalanceDisplayed() {
        return true;
    },
});
