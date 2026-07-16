# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo.addons.point_of_sale.tests.common import TestPoSCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPosProductBom(TestPoSCommon):

    def setUp(self):
        super(TestPosProductBom, self).setUp()
        self.config = self.basic_config

        # 1. Create Raw Materials (Materia Prima)
        # These are storable products that will act as ingredients
        self.raw_material_1 = self.create_product(
            name='Raw Material 1 (Dough)',
            category=self.categ_basic,
            lst_price=10.0,
            standard_price=5.0
        )
        self.raw_material_2 = self.create_product(
            name='Raw Material 2 (Tomato Sauce)',
            category=self.categ_basic,
            lst_price=15.0,
            standard_price=7.5
        )

        # 2. Adjust/Create Inventory for Raw Materials
        # We start with 50 units for each raw material
        self.adjust_inventory(
            [self.raw_material_1, self.raw_material_2],
            [50.0, 50.0]
        )

        # 3. Create Finished Product (Plato/Dish)
        # It must be marked as POS BoM Product
        self.finished_dish = self.create_product(
            name='Delicious Pizza',
            category=self.categ_basic,
            lst_price=40.0,
            standard_price=20.0
        )
        self.finished_dish.write({
            'is_pos_bom': True,
            'available_in_pos': True,
        })

        # 4. Create POS BOM Structure for the Finished Product
        self.pos_bom = self.env['pos.product.bom'].create({
            'product_id': self.finished_dish.id,
            'product_qty': 1.0,
            'product_uom_id': self.finished_dish.uom_id.id,
        })
        self.pos_bom_line_1 = self.env['pos.product.bom.line'].create({
            'pos_bom_id': self.pos_bom.id,
            'product_id': self.raw_material_1.id,
            'product_qty': 2.0,  # 2 units of Dough per Pizza
            'product_uom_id': self.raw_material_1.uom_id.id,
        })
        self.pos_bom_line_2 = self.env['pos.product.bom.line'].create({
            'pos_bom_id': self.pos_bom.id,
            'product_id': self.raw_material_2.id,
            'product_qty': 3.0,  # 3 units of Tomato Sauce per Pizza
            'product_uom_id': self.raw_material_2.uom_id.id,
        })
        self.pos_bom.confirm_bom()

    def test_pos_bom_flow(self):
        """
        Test that selling a POS BOM product:
        - Correctly registers the POS Sale (Venta en el PDV) for the client.
        - Generates the appropriate stock moves for the BoM components (ingredients).
        - Correctly consumes the raw materials (inventario de materia prima).
        - Generates correct accounting entries (asientos contables).
        """

        # We will sell 2 units of Delicious Pizza (total price 80.0)
        # This should consume:
        # - Raw Material 1: 2 * 2.0 = 4.0 units
        # - Raw Material 2: 2 * 3.0 = 6.0 units

        def _before_closing_cb():
            # Verify the order exists and is paid
            self.assertEqual(1, self.pos_session.order_count)
            order = self.pos_session.order_ids[0]
            self.assertEqual(order.state, 'paid')
            self.assertEqual(order.partner_id.id, self.customer.id)

            # Verify that stock picking has been generated
            self.assertTrue(order.picking_ids, "Stock picking should be generated for the POS order.")
            picking = order.picking_ids[0]
            self.assertEqual(picking.state, 'done', "Picking state should be done.")

            # Verify that the stock moves include the components (materia prima)
            move_products = picking.move_ids.mapped('product_id')
            self.assertIn(self.finished_dish, move_products)
            self.assertIn(self.raw_material_1, move_products)
            self.assertIn(self.raw_material_2, move_products)

            # Verify moved quantities
            move_dish = picking.move_ids.filtered(lambda m: m.product_id == self.finished_dish)
            self.assertEqual(sum(move_dish.mapped('quantity')), 2.0)

            move_rm1 = picking.move_ids.filtered(lambda m: m.product_id == self.raw_material_1)
            self.assertEqual(sum(move_rm1.mapped('quantity')), 4.0)

            move_rm2 = picking.move_ids.filtered(lambda m: m.product_id == self.raw_material_2)
            self.assertEqual(sum(move_rm2.mapped('quantity')), 6.0)

            # Verify the remaining inventory of raw materials:
            # - Raw Material 1: 50.0 - 4.0 = 46.0
            # - Raw Material 2: 50.0 - 6.0 = 44.0
            self.assertEqual(self.raw_material_1.qty_available, 46.0)
            self.assertEqual(self.raw_material_2.qty_available, 44.0)

        # Run the test case using Odoo's _run_test framework
        self._run_test({
            'payment_methods': self.cash_pm1,
            'orders': [
                {
                    'pos_order_lines_ui_args': [(self.finished_dish, 2)],
                    'payments': [(self.cash_pm1, 80.0)],
                    'customer': self.customer,
                    'uuid': '00100-010-0001'
                },
            ],
            'before_closing_cb': _before_closing_cb,
            'journal_entries_before_closing': {},
            'journal_entries_after_closing': {
                'session_journal_entry': {
                    'line_ids': [
                        {'account_id': self.sales_account.id, 'partner_id': False, 'debit': 0, 'credit': 80.0, 'reconciled': False},
                        {'account_id': self.cash_pm1.receivable_account_id.id, 'partner_id': False, 'debit': 80.0, 'credit': 0, 'reconciled': True},
                    ],
                },
                'cash_statement': [
                    ((80.0, ), {
                        'line_ids': [
                            {'account_id': self.cash_pm1.journal_id.default_account_id.id, 'partner_id': False, 'debit': 80.0, 'credit': 0, 'reconciled': False},
                            {'account_id': self.cash_pm1.receivable_account_id.id, 'partner_id': False, 'debit': 0, 'credit': 80.0, 'reconciled': True},
                        ]
                    })
                ],
                'bank_payments': [],
            },
        })
