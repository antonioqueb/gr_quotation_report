# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    x_gr_quotation_logo = fields.Binary(
        string="Logotipo de cotización GR",
        help="Imagen centrada en el encabezado de la 'Cotización Getting "
             "Ready' (monograma + wordmark). Si se deja vacío se usa el logo "
             "general de la compañía.")
    x_gr_logo_includes_wordmark = fields.Boolean(
        string="El logotipo ya incluye el texto",
        default=False,
        help="Actívelo si 'x_gr_quotation_logo' ya contiene los textos "
             "'GETTING READY' y 'VANITY EXPERIENCE'. Si se deja desactivado, "
             "el reporte agrega esos textos debajo de la imagen.")
    x_gr_social_instagram = fields.Char(
        string="Instagram (cotización GR)",
        help="Usuario de Instagram mostrado en el pie corporativo del PDF, "
             "por ejemplo @gettingready_mx.")

    def _gr_footer_locality(self):
        self.ensure_one()
        parts = [self.city, self.state_id.name, self.country_id.name]
        return ", ".join(p for p in parts if p)

    def _gr_footer_contact_line(self):
        self.ensure_one()
        parts = [self.phone, self.x_gr_social_instagram, self.email]
        return " - ".join(p for p in parts if p)
