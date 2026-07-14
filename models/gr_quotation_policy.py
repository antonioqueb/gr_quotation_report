# -*- coding: utf-8 -*-
from odoo import api, fields, models


class GrQuotationPolicy(models.Model):
    """Configurable commercial policy shown on the GR quotation report.

    Each record is one numbered point of the "POLÍTICAS" section. Content is
    stored as HTML so a policy can hold a nested bullet sub-list (as in the
    reference document, point 5). Records are combined into a single ordered
    list at print time; see ``sale.order._gr_render_policies_html``.
    """

    _name = "gr.quotation.policy"
    _description = "Política comercial de cotización (Getting Ready)"
    _order = "sequence, id"

    name = fields.Char(
        string="Referencia interna", required=True,
        help="Título corto solo para identificar la política en este listado; "
             "no se imprime en el PDF.")
    sequence = fields.Integer(string="Secuencia", default=10)
    content = fields.Html(
        string="Texto", required=True, sanitize=True, sanitize_style=True,
        help="Texto de la política tal como debe aparecer numerado en el PDF. "
             "Puede incluir una sublista con viñetas (<ul><li>...).")
    active = fields.Boolean(string="Activa", default=True)
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda s: s.env.company,
        help="Déjelo vacío para que la política aplique a todas las compañías.")
