# -*- coding: utf-8 -*-
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests.common import tagged


@tagged("post_install", "-at_install")
class TestGrQuotationPayments(AccountTestInvoicingCommon):
    """PAGADO / EXCEDENTE must reflect real posted invoices, never a guess."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({
            "name": "Set de sillas",
            "type": "consu",
            "rent_ok": True,
            "list_price": 1000.0,
        })
        cls.order = cls.env["sale.order"].create({
            "partner_id": cls.partner_a.id,
            "company_id": cls.company_data["company"].id,
        })
        cls.env["sale.order.line"].create({
            "order_id": cls.order.id,
            "product_id": cls.product.id,
            "name": cls.product.name,
            "product_uom_qty": 1,
            "price_unit": 1000.0,
        })
        cls.order.action_confirm()

    def _invoice_and_pay(self, amount):
        invoice = self.order._create_invoices()
        invoice.action_post()
        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"amount": amount})
        payment_register._create_payments()
        return invoice

    def test_no_payments_yet(self):
        self.assertEqual(self.order.x_amount_paid, 0.0)
        self.assertEqual(self.order.x_amount_overpaid, 0.0)

    def test_partial_payment_is_not_shown_as_overpayment(self):
        self._invoice_and_pay(400.0)
        self.order.invalidate_recordset()
        self.assertAlmostEqual(self.order.x_amount_paid, 400.0, places=2)
        self.assertEqual(self.order.x_amount_overpaid, 0.0)

    def test_full_payment(self):
        self._invoice_and_pay(1000.0)
        self.order.invalidate_recordset()
        self.assertAlmostEqual(self.order.x_amount_paid, 1000.0, places=2)
        self.assertEqual(self.order.x_amount_overpaid, 0.0)

    def test_overpayment_is_isolated_from_total(self):
        self._invoice_and_pay(1200.0)
        self.order.invalidate_recordset()
        self.assertAlmostEqual(self.order.x_amount_paid, 1200.0, places=2)
        self.assertAlmostEqual(self.order.x_amount_overpaid, 200.0, places=2)
