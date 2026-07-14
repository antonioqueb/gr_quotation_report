{
    "name": "GR - Reporte de Cotización",
    "version": "19.0.12.0.0",
    "category": "Sales/Sales",
    "summary": "Cotización PDF editorial de Getting Ready para órdenes de venta/renta",
    "description": """
GR Quotation Report
====================

Reporte QWeb dinámico "Cotización Getting Ready" para ``sale.order`` (renta de
eventos), construido sobre los modelos y campos ya existentes en
``aq_rental_serial_planning``. Por decisión explícita del cliente, este
módulo NO agrega una acción de reporte adicional: personaliza en el lugar la
acción estándar ``sale.action_report_saleorder`` (mismo ``ir.actions.report``,
solo se le cambian ``report_name``/``paperformat_id``), de modo que Imprimir,
Enviar por correo y la vista previa usan automáticamente este diseño sin
tocar plantillas de correo ni desvincular nada.

* Usa el layout de encabezado/pie POR DEFECTO de Odoo (``web.external_layout``,
  configurable en Ajustes > Diseño de Documentos), con logo, dirección de la
  compañía, texto de pie y numeración de página automáticos en cada hoja.
* Fila de "informaciones" con folio y fecha de cotización (mismo patrón que
  el reporte estándar de venta).
* Bloque de contratante / evento / montaje-desmontaje.
* Tabla de productos con fotografía, duración, precio, impuestos y total
  (cantidad de líneas dinámica).
* Resumen económico (subtotal, descuentos, impuestos, pagado, excedente).
* Políticas comerciales configurables (modelo ``gr.quotation.policy``), con
  copia congelada al confirmar la cotización.
* Espacios de firma física.
""",
    "author": "AlphaQueb",
    "website": "https://alphaqueb.com",
    "license": "LGPL-3",
    "depends": [
        "aq_rental_serial_planning",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/report_paperformat.xml",
        "report/gr_external_layout.xml",
        "report/gr_quotation_report_templates.xml",
        "report/ir_actions_report.xml",
        "data/gr_quotation_policy_data.xml",
        "views/gr_quotation_policy_views.xml",
        "views/sale_order_views.xml",
    ],
    "application": False,
    "installable": True,
}
