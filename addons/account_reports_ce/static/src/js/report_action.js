/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class AccountReportAction extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            reportData: null,
            loading: true,
        });

        // Params from action context
        this.reportContext = this.props.action.context || {};

        onWillStart(async () => {
            await this.loadReportData();
        });
    }

    async loadReportData() {
        this.state.loading = true;
        try {
            // In a real scenario we'd call a model method to fetch computed numbers
            // Example:
            // const data = await this.orm.call("account.financial.report.ce", "get_report_data", [this.reportContext.report_id, this.reportContext]);
            // For now, mockup data
            this.state.reportData = [
                { id: 1, name: "TEST DATA", amount: 1000 },
            ];
        } catch (e) {
            console.error(e);
        }
        this.state.loading = false;
    }

    goBack() {
        this.action.doAction({ type: 'ir.actions.act_window_close' });
    }
}

AccountReportAction.template = "account_reports_ce.AccountReportAction";
AccountReportAction.props = { ...standardActionServiceProps };

registry.category("actions").add("account_reports_ce_action", AccountReportAction);
