# -*- coding: utf-8 -*-
import re

from markupsafe import Markup

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # ------------------------------------------------------------------
    # New fields required by the "Cotización Getting Ready" report that do
    # not already exist on sale.order / aq_rental_serial_planning.
    #
    # Event date, assembly/disassembly dates, event type and the delivery
    # address are intentionally NOT duplicated here: they are already
    # provided by aq_rental_serial_planning as x_event_start, x_block_start,
    # x_block_end, x_event_type_id and x_event_location.
    # ------------------------------------------------------------------
    x_contracting_partner_id = fields.Many2one(
        "res.partner", string="Contratante",
        help="Persona que contrata el evento cuando es distinta del cliente "
             "de la cotización. Si se deja vacío se usa 'Cliente'.")
    x_event_coordinator = fields.Char(
        string="Coordinación / Wedding Planner",
        help="Nombre del coordinador o wedding planner a cargo del evento.")
    x_additional_contact_phone = fields.Char(
        string="Teléfono de contacto adicional",
        help="Teléfono adicional del lugar de montaje, mostrado en el PDF de "
             "la cotización.")

    x_policies_snapshot = fields.Html(
        string="Políticas aplicadas (congeladas)", copy=False, sanitize=True,
        help="Copia de las políticas comerciales vigentes al momento de "
             "confirmar la cotización. Una vez confirmada, el PDF usa esta "
             "copia en lugar de las políticas activas actuales, para que "
             "cambios futuros no alteren documentos históricos.")

    x_amount_gross_subtotal = fields.Monetary(
        string="Subtotal bruto", compute="_compute_gr_amounts",
        currency_field="currency_id",
        help="Suma de cantidad x precio unitario de lista, antes de "
             "descuentos de línea e impuestos.")
    x_amount_discount_total = fields.Monetary(
        string="Descuentos", compute="_compute_gr_amounts",
        currency_field="currency_id",
        help="Suma de los descuentos de línea realmente aplicados.")
    x_amount_paid = fields.Monetary(
        string="Pagado", compute="_compute_gr_paid_amounts",
        currency_field="currency_id",
        help="Importe efectivamente pagado según las facturas publicadas "
             "vinculadas a esta orden (ver limitación en "
             "_compute_gr_paid_amounts).")
    x_amount_overpaid = fields.Monetary(
        string="Excedente", compute="_compute_gr_paid_amounts",
        currency_field="currency_id",
        help="Importe pagado por encima del total de la cotización. No es "
             "un saldo pendiente: si el pago es menor al total, este campo "
             "es 0.")

    @api.depends("order_line.price_unit", "order_line.product_uom_qty",
                 "order_line.discount", "order_line.display_type",
                 "order_line.is_downpayment")
    def _compute_gr_amounts(self):
        for order in self:
            lines = order.order_line.filtered(
                lambda l: not l.display_type and not l.is_downpayment)
            gross = sum((l.price_unit or 0.0) * (l.product_uom_qty or 0.0) for l in lines)
            discount = sum(
                (l.price_unit or 0.0) * (l.product_uom_qty or 0.0) * (l.discount or 0.0) / 100.0
                for l in lines)
            order.x_amount_gross_subtotal = gross
            order.x_amount_discount_total = discount

    @api.depends("invoice_ids.state", "invoice_ids.amount_residual",
                 "invoice_ids.amount_total", "invoice_ids.currency_id",
                 "amount_total")
    def _compute_gr_paid_amounts(self):
        """Best-effort 'amount paid' / 'overpayment' for the report.

        Limitation: this sums ``amount_total - amount_residual`` on posted,
        non-cancelled customer invoices/credit notes linked to the order,
        converted to the order currency at each invoice's accounting date.
        It does not inspect individual ``account.payment`` records, so a
        payment registered but not yet reconciled to an invoice is not
        reflected here. If a more precise, payment-level reconciliation is
        required, extend this method rather than editing the report.
        """
        for order in self:
            paid = 0.0
            for move in order.invoice_ids:
                if move.state != "posted":
                    continue
                move_paid = (move.amount_total - move.amount_residual)
                if move.currency_id != order.currency_id:
                    move_paid = move.currency_id._convert(
                        move_paid, order.currency_id, order.company_id,
                        move.invoice_date or fields.Date.context_today(order))
                if move.move_type == "out_refund":
                    paid -= move_paid
                else:
                    paid += move_paid
            order.x_amount_paid = paid
            order.x_amount_overpaid = max(0.0, paid - order.amount_total)

    # ------------------------------------------------------------------
    # Report helpers (kept out of QWeb on purpose)
    # ------------------------------------------------------------------
    def _gr_get_contracting_partner(self):
        self.ensure_one()
        return self.x_contracting_partner_id or self.partner_id

    def _gr_get_contact_phone(self):
        self.ensure_one()
        partner = self._gr_get_contracting_partner()
        return partner.phone or partner.mobile or self.partner_id.phone or self.partner_id.mobile or ""

    def _gr_get_contact_email(self):
        self.ensure_one()
        partner = self._gr_get_contracting_partner()
        return partner.email or self.partner_id.email or ""

    def _gr_render_policies_html(self):
        """Build the numbered policy list from currently active policies."""
        self.ensure_one()
        Policy = self.env["gr.quotation.policy"].sudo()
        policies = Policy.search([
            ("active", "=", True),
            ("company_id", "in", [self.company_id.id, False]),
        ])
        if not policies:
            return Markup("")
        items = "".join("<li>%s</li>" % (p.content or "") for p in policies)
        return Markup("<ol class=\"gr_policy_list\">%s</ol>" % items)

    def _gr_get_policies_html(self):
        """Frozen snapshot once the order is confirmed, live list otherwise."""
        self.ensure_one()
        if self.state in ("sale", "done") and self.x_policies_snapshot:
            return Markup(self.x_policies_snapshot)
        return self._gr_render_policies_html()

    def _gr_format_date(self, value):
        """Format a Datetime field as DD-MM-YYYY in the user's timezone.

        Only the date is shown, per the reference document (no time-of-day).
        """
        if not value:
            return ""
        local_dt = fields.Datetime.context_timestamp(self, value)
        return local_dt.strftime("%d-%m-%Y")

    def _gr_report_filename(self):
        """Sanitized 'Cotizacion_GR_<folio>_<cliente>' file name (no extension)."""
        self.ensure_one()
        folio = self.name or ""
        client = self.partner_id.name or ""
        raw = "Cotizacion_GR_%s_%s" % (folio, client)
        raw = re.sub(r"[\\/*?:\"<>|]", "", raw)
        raw = re.sub(r"\s+", "_", raw).strip("_")
        return raw or "Cotizacion_GR"

    def _action_confirm(self):
        res = super()._action_confirm()
        for order in self:
            if not order.x_policies_snapshot:
                order.x_policies_snapshot = order._gr_render_policies_html()
        return res
