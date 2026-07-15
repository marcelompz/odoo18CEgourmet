import { patch } from "@web/core/utils/patch";
import { PrinterService } from "@point_of_sale/app/printer/printer_service";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { htmlToCanvas } from "@point_of_sale/app/printer/render_service";

patch(PrinterService.prototype, {
    async printWeb(el) {
        try {
            console.log('Intercepting printWeb for direct thermal printing...');
            // Convert HTML element to canvas natively using Odoo 18 render service
            const canvas = await htmlToCanvas(el, { addClass: "pos-receipt-print" });
            const image = canvas.toDataURL("image/png").replace("data:image/png;base64,", "");
            
            // Send base64 PNG to local printer server
            await fetch('http://localhost:8080', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    printer: 'ticket',
                    base64: image,
                }),
            });
            return true;
        } catch (err) {
            console.error("Error printing to local server:", err);
            // Fallback to standard Odoo print dialog
            return super.printWeb(el);
        }
    }
});

patch(PaymentScreen.prototype, {
    async _finalizeValidation() {
        const result = await super._finalizeValidation(...arguments);
        
        // If order is invoiced, trigger automatic local print
        if (this.currentOrder.is_to_invoice()) {
            console.log('Sending invoice print job to local server...');
            setTimeout(function() {
                fetch('http://localhost:8080', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        printer: 'factura',
                        filename: window.location.protocol + '//' + window.location.host + '/printing/static/src/invoice.pdf'
                    }),
                }).catch(err => console.error("Error sending invoice to local print server:", err));
            }, 5000);
        }
        
        return result;
    }
});
