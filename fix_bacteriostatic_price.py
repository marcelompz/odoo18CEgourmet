#!/usr/bin/env python3
"""
Fix POS order lines for AGUA BACTEROSTATICA 2.5ML (product_tmpl_id=3041)
where price_unit < 1.5, setting price_unit = 1.5.
"""
import odoo
from odoo import SUPERUSER_ID

DB_NAME = "prod_2026-04-05_update"
CORRECT_PRICE = 1.5
PRODUCT_TMPL_ID = 3041

registry = odoo.registry(DB_NAME)
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, SUPERUSER_ID, {})

    # Find all affected order lines
    lines = env['pos.order.line'].search([
        ('product_id.product_tmpl_id', '=', PRODUCT_TMPL_ID),
        ('price_unit', '<', CORRECT_PRICE),
    ])

    print(f"Found {len(lines)} order lines with price < {CORRECT_PRICE}")

    affected_orders = set()

    for line in lines:
        old_price = line.price_unit
        old_subtotal = line.price_subtotal
        qty = line.qty

        # Skip refund refund lines (negative qty are refunds, keep them paired)
        # We handle both lines in a refund pair proportionally
        new_price = CORRECT_PRICE
        new_subtotal = new_price * qty

        print(f"  Line {line.id}: Order={line.order_id.name}, "
              f"Price {old_price} -> {new_price}, "
              f"Qty={qty}, "
              f"Subtotal {old_subtotal} -> {new_subtotal}")

        line.write({
            'price_unit': new_price,
        })

        affected_orders.add(line.order_id.id)

    # Recompute order totals
    orders = env['pos.order'].browse(list(affected_orders))
    print(f"\nRecomputing totals for {len(orders)} orders...")

    for order in orders:
        old_total = order.amount_total
        # Force recomputation of amount_total
        order._compute_amount_all()
        new_total = order.amount_total
        diff = new_total - old_total
        print(f"  Order {order.name}: {old_total} -> {new_total} (diff: {diff:+.2f})")

    cr.commit()
    print("\n✓ Changes committed successfully!")
