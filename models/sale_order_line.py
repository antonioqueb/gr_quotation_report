# -*- coding: utf-8 -*-
import math

from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    x_gr_price_after_discount = fields.Monetary(
        string="Precio (con desc. de línea)", compute="_compute_gr_price_after_discount",
        currency_field="currency_id",
        help="Precio unitario después del descuento de línea, antes de "
             "impuestos. Usado en la columna PRECIO del reporte GR.")
    x_gr_tax_label = fields.Char(
        string="Etiqueta de impuesto", compute="_compute_gr_tax_label",
        help="Nombre comercial de los impuestos de la línea, separados por "
             "coma. Vacío si la línea no tiene impuestos.")
    x_gr_article_title = fields.Char(
        string="Título de artículo", compute="_compute_gr_article_text",
        help="Nombre comercial del producto para la columna ARTÍCULO.")
    x_gr_article_extra = fields.Text(
        string="Descripción adicional", compute="_compute_gr_article_text",
        help="Texto de la línea que no repite el nombre del producto.")
    x_gr_duration_label = fields.Char(
        string="Duración", compute="_compute_gr_duration_label",
        help="Duración del alquiler en texto (p. ej. '3 días'), calculada a "
             "partir del periodo facturable de la línea/orden.")
    x_gr_qty_label = fields.Char(
        string="Cantidad (texto)", compute="_compute_gr_qty_label",
        help="Cantidad formateada sin decimales innecesarios, con la unidad "
             "de medida cuando no es la unidad genérica.")

    @api.depends("product_uom_qty", "product_uom", "display_type")
    def _compute_gr_qty_label(self):
        for line in self:
            if line.display_type:
                line.x_gr_qty_label = ""
                continue
            qty = line.product_uom_qty or 0.0
            qty_text = "%g" % qty if qty % 1 else "%d" % int(qty)
            uom = line.product_uom
            if uom and uom.name and uom.name.lower() not in ("units", "unidades", "unidad", "unit"):
                qty_text = "%s %s" % (qty_text, uom.name)
            line.x_gr_qty_label = qty_text

    @api.depends("price_unit", "discount", "display_type")
    def _compute_gr_price_after_discount(self):
        for line in self:
            if line.display_type:
                line.x_gr_price_after_discount = 0.0
            else:
                line.x_gr_price_after_discount = (
                    (line.price_unit or 0.0) * (1.0 - (line.discount or 0.0) / 100.0))

    @api.depends("tax_id", "display_type")
    def _compute_gr_tax_label(self):
        for line in self:
            if line.display_type or not line.tax_id:
                line.x_gr_tax_label = ""
            else:
                line.x_gr_tax_label = ", ".join(t.name for t in line.tax_id if t.name)

    @api.depends("name", "product_id.display_name", "display_type")
    def _compute_gr_article_text(self):
        for line in self:
            if line.display_type:
                line.x_gr_article_title = ""
                line.x_gr_article_extra = ""
                continue
            product_name = (line.product_id.display_name or "").strip()
            full_text = (line.name or "").strip()
            title = product_name
            extra = full_text
            if full_text:
                rows = full_text.split("\n")
                if product_name and rows[0].strip() == product_name:
                    extra = "\n".join(rows[1:]).strip()
                elif not product_name:
                    title = rows[0].strip()
                    extra = "\n".join(rows[1:]).strip()
            if extra == title:
                extra = ""
            line.x_gr_article_title = title or full_text
            line.x_gr_article_extra = extra

    @api.depends("product_id", "display_type", "x_line_type",
                 "x_billable_start", "x_billable_end",
                 "order_id.x_billable_start", "order_id.x_billable_end")
    def _compute_gr_duration_label(self):
        for line in self:
            label = ""
            is_rental = line.x_line_type in ("serial_rental", "quantity_rental") or (
                not line.x_line_type and line.product_id and line.product_id.rent_ok)
            if not line.display_type and line.product_id and is_rental:
                start, end = line._get_billable_period()
                if start and end and end > start:
                    days = max(1, math.ceil((end - start).total_seconds() / 86400.0))
                    label = _("1 día") if days == 1 else _("%d días") % days
            line.x_gr_duration_label = label
