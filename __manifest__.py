{
    "name": "GR - Reporte de Cotización",
    "version": "19.0.2.0.0",
    "category": "Sales/Sales",
    "summary": "Cotización PDF editorial de Getting Ready para órdenes de venta/renta",
    "description": """
GR Quotation Report
====================

Reporte QWeb dinámico "Cotización Getting Ready" para ``sale.order`` (renta de
eventos), construido sobre los modelos y campos ya existentes en
``aq_rental_serial_planning``. Por decisión explícita del cliente, este
reporte reemplaza al reporte estándar de cotización de Odoo como acción de
Imprimir/Enviar por correo en ``sale.order`` (el reporte estándar no se
elimina, solo se desvincula de ese modelo).

* Formato de página propio (Carta, sin encabezado/pie estándar de Odoo).
* Encabezado con cliente, folio y fecha.
* Bloque de contratante / evento / montaje-desmontaje.
* Tabla de productos con fotografía, duración, precio, impuestos y total
  (cantidad de líneas dinámica).
* Resumen económico (subtotal, descuentos, impuestos, pagado, excedente).
* Políticas comerciales configurables (modelo ``gr.quotation.policy``), con
  copia congelada al confirmar la cotización.
* Espacios de firma física y pie corporativo tomado de ``res.company``.
""",
    "author": "AlphaQueb",
    "website": "https://alphaqueb.com",
    "license": "LGPL-3",
    "depends": [
        "aq_rental_serial_planning",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/report_paperformat.xml",
        "report/gr_quotation_report_templates.xml",
        "report/ir_actions_report.xml",
        "data/gr_quotation_policy_data.xml",
        "data/sale_report_defaults.xml",
        "views/gr_quotation_policy_views.xml",
        "views/res_company_views.xml",
        "views/sale_order_views.xml",
    ],
    "application": False,
    "installable": True,
}
