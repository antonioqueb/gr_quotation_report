# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class GrQuotationReportCommon(TransactionCase):
    """Shared fixtures for the GR quotation report tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ReportModel = cls.env["ir.actions.report"]
        cls.report_xmlid = "gr_quotation_report.report_gr_quotation_document"

        cls.event_type = cls.env["rental.event.type"].create({"name": "Boda"})
        cls.tax_iva = cls.env["account.tax"].create({
            "name": "IVA 16%",
            "amount": 16.0,
            "amount_type": "percent",
            "type_tax_use": "sale",
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Eugenia Villarreal",
            "phone": "8110000000",
            "email": "eugenia@example.com",
        })
        cls.coordinator_partner = cls.env["res.partner"].create({
            "name": "Alexia Treto",
        })
        cls.partner_incomplete = cls.env["res.partner"].create({"name": "Cliente Sin Datos"})

        # A simple rentable product; no serial/stock machinery is needed to
        # exercise the report itself.
        cls.product_with_image = cls.env["product.product"].create({
            "name": "Silla Manhattan",
            "type": "consu",
            "rent_ok": True,
            "list_price": 100.0,
            "taxes_id": [(6, 0, cls.tax_iva.ids)],
            # 1x1 transparent PNG, just to prove the image branch renders.
            "image_1920": (
                b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
                b"+A8AAQUBAScY42YAAAAASUVORK5CYII="
            ),
        })
        cls.product_no_image = cls.env["product.product"].create({
            "name": "Mesa Redonda 1.5m",
            "type": "consu",
            "rent_ok": True,
            "list_price": 250.0,
            "taxes_id": [(6, 0, cls.tax_iva.ids)],
        })

    def _make_order(self, partner=None, n_lines=1, currency=None, with_discount=False,
                     long_description=False):
        start = datetime(2026, 12, 30, 9, 0)
        end = datetime(2026, 12, 31, 20, 0)
        vals = {
            "partner_id": (partner or self.partner).id,
            "x_is_event_rental": True,
            "x_event_type_id": self.event_type.id,
            "x_event_name": "Boda Villarreal",
            "x_event_location": "Rio Pesqueria 156, San Pedro Garza García, N.L.",
            "x_event_start": start,
            "x_event_end": end,
            "x_billable_start": start,
            "x_billable_end": end,
            "x_block_start": start - timedelta(hours=6),
            "x_block_end": end + timedelta(hours=6),
            "x_contracting_partner_id": self.coordinator_partner.id,
            "x_event_coordinator": "Elemento 3",
            "x_additional_contact_phone": "8112223344",
        }
        if currency:
            pricelist = self.env["product.pricelist"].create({
                "name": "GR-%s" % currency.name,
                "currency_id": currency.id,
            })
            vals["pricelist_id"] = pricelist.id
        order = self.env["sale.order"].create(vals)
        products = [self.product_with_image, self.product_no_image]
        for i in range(n_lines):
            product = products[i % 2]
            name = product.name
            if long_description:
                name = (product.name + "\n" + ("Lorem ipsum dolor sit amet, " * 8).strip())
            self.env["sale.order.line"].create({
                "order_id": order.id,
                "product_id": product.id,
                "name": name,
                "product_uom_qty": 1,
                "price_unit": product.list_price,
                "discount": 10.0 if with_discount else 0.0,
                "tax_ids": [(6, 0, product.taxes_id.ids)],
            })
        return order

    def _render_html(self, order):
        html, _report_type = self.ReportModel._render_qweb_html(self.report_xmlid, order.ids)
        return html.decode() if isinstance(html, bytes) else html


class TestGrQuotationReportRendering(GrQuotationReportCommon):

    def test_report_renders_with_one_line(self):
        order = self._make_order(n_lines=1)
        html = self._render_html(order)
        self.assertIn(order.name, html)
        self.assertIn("POLÍTICAS".upper(), html.upper())

    def test_report_renders_with_eight_lines(self):
        order = self._make_order(n_lines=8)
        html = self._render_html(order)
        # every product line must appear once
        self.assertEqual(html.count("Silla Manhattan"), 4)
        self.assertEqual(html.count("Mesa Redonda 1.5m"), 4)

    def test_report_renders_with_more_than_twenty_lines(self):
        order = self._make_order(n_lines=25)
        html = self._render_html(order)
        self.assertEqual(len(order.order_line), 25)
        # should not raise and should still contain the summary block
        self.assertIn("EXCEDENTE", html.upper())

    def test_product_with_image_renders_img_tag(self):
        order = self._make_order(n_lines=1)
        html = self._render_html(order)
        self.assertIn("gr_product_img", html)

    def test_product_without_image_uses_placeholder_not_broken_icon(self):
        order = self.env["sale.order"].create({"partner_id": self.partner.id})
        self.env["sale.order.line"].create({
            "order_id": order.id,
            "product_id": self.product_no_image.id,
            "name": self.product_no_image.name,
            "product_uom_qty": 1,
            "price_unit": self.product_no_image.list_price,
        })
        html = self._render_html(order)
        self.assertIn("gr_img_placeholder", html)

    def test_long_description_does_not_repeat_product_name(self):
        order = self._make_order(n_lines=1, long_description=True)
        line = order.order_line[0]
        self.assertTrue(line.x_gr_article_extra)
        self.assertNotIn(line.product_id.display_name, line.x_gr_article_extra)

    def test_partner_with_incomplete_contact_info(self):
        order = self._make_order(partner=self.partner_incomplete, n_lines=1)
        order.x_contracting_partner_id = False
        html = self._render_html(order)
        # no phone/email on file: must not print False/None
        self.assertNotIn(">False<", html)
        self.assertNotIn(">None<", html)

    def test_line_discount_is_reflected_in_amounts(self):
        order = self._make_order(n_lines=2, with_discount=True)
        self.assertGreater(order.x_amount_discount_total, 0.0)
        self.assertAlmostEqual(
            order.x_amount_gross_subtotal - order.x_amount_discount_total,
            order.amount_untaxed, places=2)

    def test_iva_tax_label_is_not_a_technical_id(self):
        order = self._make_order(n_lines=1)
        line = order.order_line[0]
        self.assertIn("IVA", line.x_gr_tax_label.upper())
        self.assertFalse(line.x_gr_tax_label.isdigit())

    def test_extensive_policies_render_as_ordered_list(self):
        Policy = self.env["gr.quotation.policy"]
        Policy.search([]).write({"active": False})
        for i in range(30):
            Policy.create({
                "name": "Política %s" % i, "sequence": i,
                "content": "<p>Texto de política número %s.</p>" % i,
            })
        order = self._make_order(n_lines=1)
        html = self._render_html(order)
        self.assertEqual(html.count("gr_policy_list"), 1)
        self.assertIn("Texto de política número 29.", html)

    def test_currency_other_than_mxn(self):
        usd = self.env.ref("base.USD")
        usd.active = True
        order = self._make_order(n_lines=1, currency=usd)
        self.assertEqual(order.currency_id, usd)
        html = self._render_html(order)
        self.assertIn(order.name, html)

    def test_qweb_template_loads_without_error(self):
        order = self._make_order(n_lines=3)
        try:
            self._render_html(order)
        except Exception as exc:  # pragma: no cover - failure path
            self.fail("El template QWeb no cargó correctamente: %s" % exc)

    def test_report_action_is_bound_to_sale_order(self):
        action = self.env.ref("gr_quotation_report.action_report_gr_quotation")
        self.assertEqual(action.model, "sale.order")
        self.assertEqual(action.report_type, "qweb-pdf")
        self.assertEqual(action.binding_model_id.model, "sale.order")

    def test_gr_report_is_the_only_one_bound_to_sale_order(self):
        standard_action = self.env.ref("sale.action_report_saleorder")
        self.assertFalse(
            standard_action.binding_model_id,
            "El reporte estándar de Odoo debe quedar desvinculado de "
            "sale.order para que 'Imprimir' use únicamente la Cotización "
            "Getting Ready.")

    def test_gr_report_is_used_for_send_by_email(self):
        gr_action = self.env.ref("gr_quotation_report.action_report_gr_quotation")
        for tmpl_xmlid in ("sale.email_template_edi_sale", "sale.mail_template_sale_confirmation"):
            template = self.env.ref(tmpl_xmlid)
            self.assertEqual(
                template.report_template_ids.ids, gr_action.ids,
                "%s debe adjuntar únicamente la Cotización Getting Ready." % tmpl_xmlid)

    def test_report_body_requests_full_width(self):
        # web.report_layout renders <body class="container-fluid"> only when
        # full_width is truthy; otherwise it falls back to the Bootstrap
        # "container" class, which is what shrank the page to ~75-80% width.
        order = self._make_order(n_lines=1)
        html = self._render_html(order)
        self.assertIn("container-fluid", html)
        self.assertNotIn('o_body_html container overflow-x-hidden', html)

    def test_report_filename_is_sanitized(self):
        order = self._make_order(n_lines=1)
        order.partner_id.name = 'Cliente "Raro" / Ex:tra*ño?'
        filename = order._gr_report_filename()
        for bad_char in '\\/*?:"<>|':
            self.assertNotIn(bad_char, filename)
        self.assertTrue(filename.startswith("Cotizacion_GR_"))

    def test_no_false_or_none_literals_in_output(self):
        order = self.env["sale.order"].create({"partner_id": self.partner_incomplete.id})
        self.env["sale.order.line"].create({
            "order_id": order.id,
            "product_id": self.product_no_image.id,
            "name": self.product_no_image.name,
            "product_uom_qty": 1,
            "price_unit": self.product_no_image.list_price,
        })
        html = self._render_html(order)
        self.assertNotIn(">False<", html)
        self.assertNotIn(">None<", html)
        self.assertNotIn("0-0-00", html)
