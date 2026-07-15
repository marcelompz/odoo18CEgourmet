# POS Central Cashier

**Version:** 18.0.1.0.0  
**Author:** Crossnexion E.A.S.  
**License:** OPL-1  

## Summary

This module implements a **Counter-to-Cashier workflow** for Odoo Point of Sale. It allows you to separate the order-taking process from the payment process across different POS terminals.

### Use Case

- **Counter POS (Mostrador):** Staff at counters can take orders and generate pre-bills (precuentas), but cannot process payments.
- **Central Cashier POS (Caja Principal):** A dedicated cashier terminal can retrieve all pending orders from any counter, load them with full details, and process payments.

This is ideal for restaurants, food courts, retail environments, or any business where you want to separate order taking from payment collection.

---

## Features

- ✅ Mark orders as "Pending Payment" from Counter POS terminals
- ✅ Auto-generated pre-bill reference numbers (e.g., `PREC-00001`)
- ✅ Receipt printing with "PRECUENTA - PENDIENTE DE PAGO" label for pending orders
- ✅ Search and retrieve pending orders from Central Cashier POS
- ✅ Load pending orders with full line items at cashier terminal
- ✅ Automatic order state synchronization between counter and cashier
- ✅ Mutual exclusion: A POS cannot be both Counter and Cashier simultaneously
- ✅ Payment protection: Counter POS cannot directly pay pending orders

---

## Dependencies

- `point_of_sale` - Odoo Point of Sale
- `pos_restaurant` - Odoo POS Restaurant

---

## Installation

1. Ensure the module is in your Odoo addons path.
2. Go to **Apps** → Update Apps List.
3. Search for **POS Central Cashier**.
4. Click **Activate** or **Install**.

---

## Configuration

### Step 1: Configure Counter POS

1. Go to **Point of Sale** → **Configuration** → **Point of Sale**.
2. Open or create the POS terminal that will act as a **Counter** (e.g., "Bar Counter", "Table Orders").
3. Scroll to the **Caja Principal y Mostrador** section.
4. ✅ Check **PDV Mostrador** (Counter POS).
5. ❌ Leave **PDV Caja Principal** unchecked.
6. Save.

### Step 2: Configure Central Cashier POS

1. Go to **Point of Sale** → **Configuration** → **Point of Sale**.
2. Open or create the POS terminal that will act as the **Central Cashier** (e.g., "Main Cashier", "Central Register").
3. Scroll to the **Caja Principal y Mostrador** section.
4. ❌ Leave **PDV Mostrador** unchecked.
5. ✅ Check **PDV Caja Principal** (Central Cashier POS).
6. Save.

### ⚠️ Important

- A POS **cannot** be both Counter and Central Cashier at the same time. The system will show a validation error if you try to enable both.
- You can have **multiple** Counter POS terminals, but typically only **one** Central Cashier POS.

---

## Usage

### Workflow at Counter POS (Mostrador)

1. **Open the POS session** at the Counter terminal.
2. **Create an order** by adding products/items as usual.
3. Instead of clicking "Pay", click the **"Precuenta y Pendiente"** button (orange button with print icon).
4. The system will:
   - Sync the order to the server
   - Generate a pre-bill reference (e.g., `PREC-00001`)
   - Mark the order as pending payment
   - Show the receipt screen with "PRECUENTA - PENDIENTE DE PAGO" label
5. **Print the receipt** and give it to the customer.

### Workflow at Central Cashier POS (Caja Principal)

1. **Open the POS session** at the Cashier terminal.
2. Click the **"Buscar Órdenes"** (Search Orders) button in the navbar.
3. A dialog will appear showing all pending orders.
4. **Search** by pre-bill reference or customer name (optional).
5. **Click on the order** you want to process.
6. The system will:
   - Load all order details (customer, products, quantities, prices, discounts, notes)
   - Navigate to the Payment Screen
7. **Process the payment** as normal (cash, card, etc.).
8. Once paid, both the cashier order and the original counter order are marked as paid.

---

## Technical Details

### New Fields on `pos.config`

| Field | Type | Description |
|-------|------|-------------|
| `is_counter_pos` | Boolean | Enables "Precuenta y Pendiente" button |
| `is_central_cashier` | Boolean | Enables "Buscar Órdenes" search button |

### New Fields on `pos.order`

| Field | Type | Description |
|-------|------|-------------|
| `is_pending_payment` | Boolean | Marks order as pending payment |
| `precuenta_ref` | Char | Pre-bill reference (auto-generated, e.g., `PREC-00001`) |
| `source_order_id` | Many2one (`pos.order`) | Links cashier order back to original counter order |

### Sequence

- **Code:** `pos.central.cashier.precuenta`
- **Prefix:** `PREC-`
- **Padding:** 5 digits
- **Format:** `PREC-00001`, `PREC-00002`, etc.

### Backend Methods

| Method | Description |
|--------|-------------|
| `mark_order_pending(order_id)` | Marks an order as pending and generates precuenta_ref |
| `search_pending_orders_for_pos(query="", limit=30)` | Searches pending orders by reference or customer name |
| `export_pending_order_payload(order_id)` | Exports full order data for cashier POS to load |
| `complete_pending_order_payment()` | Marks both counter and cashier orders as paid |

---

## File Structure

```
pos_central_cashier/
├── __init__.py
├── __manifest__.py
├── data/
│   └── sequence.xml              # Pre-bill reference sequence
├── models/
│   ├── __init__.py
│   ├── pos_config.py             # POS configuration fields
│   └── pos_order.py              # Order fields and business logic
├── static/
│   └── src/
│       ├── js/
│       │   ├── custom_pos_buttons.js      # Counter "Precuenta" button
│       │   ├── custom_pos_screens.js      # Cashier pending orders dialog
│       │   ├── payment_screen_inherit.js  # Payment validation
│       │   └── receipt_patch.js           # Receipt data patch
│       └── xml/
│           ├── custom_pos_templates.xml   # UI templates
│           └── pos_ticket_inherit.xml     # Receipt template
└── views/
    └── pos_config_views.xml       # POS config form view
```

---

## Troubleshooting

### "Order ID not available" error at Counter
- Ensure the POS session is open and synced.
- Check network connectivity to the Odoo server.
- Try syncing manually by refreshing the POS session.

### No pending orders appear at Cashier
- Verify orders were actually marked as pending at the Counter POS.
- Check that the Counter POS has `is_counter_pos` enabled.
- Check the `is_pending_payment` field on orders in the backend.

### "A POS cannot be both Counter and Central Cashier" error
- This is intentional. A POS must be **either** a Counter **or** a Cashier, not both.
- Uncheck one of the two fields to resolve.

### Pre-bill references are not sequential
- Sequences may be shared across companies if `company_id` is not set.
- The sequence is set to company-independent (`company_id = False`) by design to work across all companies.

---

## Support

For issues or feature requests, contact **Crossnexion E.A.S.**

---

## License

This software is proprietary and can only be used with a valid license purchased from the authors. See the `LICENCE` file for details.
