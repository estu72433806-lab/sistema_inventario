"""
Servicio para la generación de comprobantes de venta en PDF utilizando ReportLab.
Emite Boletas y Facturas para el ámbito académico con todos los datos comerciales:
Nombre del negocio, número de comprobante, fecha, cliente, productos, cantidades,
precios, descuento y total pagado.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFService:
    @staticmethod
    def obtener_carpeta_comprobantes():
        """Retorna y asegura la existencia de la carpeta 'documentos_generados/comprobantes'."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        carpeta = os.path.join(base_dir, "documentos_generados", "comprobantes")
        os.makedirs(carpeta, exist_ok=True)
        return carpeta

    @classmethod
    def generar_comprobante_pdf(cls, venta_dict, ruta_salida=None):
        """
        Genera un comprobante en PDF (Boleta o Factura) con ReportLab:
        - venta_dict: diccionario con cabecera y lista de 'detalles'
        - ruta_salida: path opcional; si no se provee, se guarda en 'documentos_generados/comprobantes/'
        """
        if not ruta_salida:
            carpeta = cls.obtener_carpeta_comprobantes()
            num_seguro = str(venta_dict.get('numero_comprobante', '000000')).replace('/', '_').replace('-', '_')
            ruta_salida = os.path.join(carpeta, f"Comprobante_{num_seguro}.pdf")

        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elementos = []
        estilos = getSampleStyleSheet()

        # Estilos tipográficos
        titulo_empresa = ParagraphStyle(
            'TituloEmpresa',
            parent=estilos['Heading1'],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold"
        )
        subtitulo_empresa = ParagraphStyle(
            'SubtituloEmpresa',
            parent=estilos['Normal'],
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor("#475569")
        )
        caja_tipo = ParagraphStyle(
            'CajaTipo',
            parent=estilos['Heading2'],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            alignment=1,
            fontName="Helvetica-Bold"
        )
        negrita = ParagraphStyle(
            'Negrita',
            parent=estilos['Normal'],
            fontSize=8.5,
            leading=11,
            fontName="Helvetica-Bold"
        )
        normal = ParagraphStyle(
            'Normal',
            parent=estilos['Normal'],
            fontSize=8.5,
            leading=11
        )

        # 1. Encabezado de la Empresa y Recuadro del Comprobante
        datos_empresa = [
            Paragraph("<b>TECHSTORE COMPUTADORAS S.A.C.</b>", titulo_empresa),
            Paragraph("Venta de Hardware, Laptops, Componentes y Servicio Técnico Especializado", subtitulo_empresa),
            Paragraph("Av. Tecnología 1024 - Centro Tecnológico | Teléfono: (01) 555-4321", subtitulo_empresa),
            Paragraph("Email: ventas@techstore.local | RUC: 20601234567", subtitulo_empresa)
        ]

        tipo_doc_nombre = venta_dict.get('tipo_comprobante', 'BOLETA DE VENTA').upper()
        num_doc = venta_dict.get('numero_comprobante', 'B-000001')

        caja_comprobante = [
            Paragraph("<b>RUC: 20601234567</b>", caja_tipo),
            Paragraph(f"<b>{tipo_doc_nombre}</b>", caja_tipo),
            Paragraph(f"<b>N° {num_doc}</b>", caja_tipo)
        ]

        tabla_cabecera = Table(
            [[datos_empresa, caja_comprobante]],
            colWidths=[340, 200]
        )
        tabla_cabecera.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOX', (1,0), (1,0), 1.5, colors.HexColor("#0f172a")),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor("#f8fafc")),
            ('TOPPADDING', (1,0), (1,0), 8),
            ('BOTTOMPADDING', (1,0), (1,0), 8),
        ]))
        elementos.append(tabla_cabecera)
        elementos.append(Spacer(1, 12))

        # 2. Información del Cliente y Fecha
        fecha_venta = str(venta_dict.get('fecha', ''))
        cliente_nom = str(venta_dict.get('cliente_nombre', 'Público General'))
        tipo_cliente_doc = str(venta_dict.get('tipo_documento', 'DNI/RUC'))
        num_cliente_doc = str(venta_dict.get('numero_documento', '-'))
        direccion_cli = str(venta_dict.get('direccion', '-') or '-')
        telefono_cli = str(venta_dict.get('telefono', '-') or '-')
        vendedor_nom = str(venta_dict.get('vendedor_nombre') or venta_dict.get('vendedor_username') or 'Admin')
        metodo_pago = str(venta_dict.get('metodo_pago', 'Efectivo'))

        info_cliente = [
            [
                Paragraph("<b>Fecha y Hora:</b>", negrita),
                Paragraph(fecha_venta, normal),
                Paragraph("<b>Método de Pago:</b>", negrita),
                Paragraph(metodo_pago, normal)
            ],
            [
                Paragraph("<b>Cliente:</b>", negrita),
                Paragraph(cliente_nom, normal),
                Paragraph(f"<b>{tipo_cliente_doc}:</b>", negrita),
                Paragraph(num_cliente_doc, normal)
            ],
            [
                Paragraph("<b>Dirección:</b>", negrita),
                Paragraph(direccion_cli, normal),
                Paragraph("<b>Atendido Por:</b>", negrita),
                Paragraph(vendedor_nom, normal)
            ]
        ]
        tabla_cli = Table(info_cliente, colWidths=[80, 210, 90, 160])
        tabla_cli.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elementos.append(tabla_cli)
        elementos.append(Spacer(1, 12))

        # 3. Detalle de Productos Vendidos
        encabezados = [
            Paragraph("<b>Cant.</b>", negrita),
            Paragraph("<b>Código</b>", negrita),
            Paragraph("<b>Descripción del Producto</b>", negrita),
            Paragraph("<b>P. Unit.</b>", negrita),
            Paragraph("<b>Subtotal</b>", negrita)
        ]
        items_data = [encabezados]

        for item in venta_dict.get('detalles', []):
            cant = item.get('cantidad', 1)
            cod = item.get('codigo', '-')
            desc = f"{item.get('nombre', '')}"
            if item.get('marca'):
                desc += f" ({item['marca']})"
            pu = float(item.get('precio_unitario', 0.0))
            sub = float(item.get('subtotal', 0.0))

            items_data.append([
                Paragraph(str(cant), normal),
                Paragraph(str(cod), normal),
                Paragraph(desc, normal),
                Paragraph(f"S/ {pu:.2f}", normal),
                Paragraph(f"S/ {sub:.2f}", normal)
            ])

        tabla_prod = Table(items_data, colWidths=[40, 75, 275, 75, 75])
        tabla_prod.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        elementos.append(tabla_prod)
        elementos.append(Spacer(1, 10))

        # 4. Totales, Descuento y Liquidación
        subtotal_val = float(venta_dict.get('subtotal', 0.0))
        descuento_val = float(venta_dict.get('descuento', 0.0))
        impuesto_val = float(venta_dict.get('impuesto', 0.0))
        total_val = float(venta_dict.get('total', 0.0))

        totales_data = [
            ["", Paragraph("<b>Subtotal Bruto:</b>", negrita), f"S/ {subtotal_val:.2f}"]
        ]
        if descuento_val > 0:
            totales_data.append([
                "", Paragraph("<b>Descuento Comercial:</b>", negrita), f"-S/ {descuento_val:.2f}"
            ])
        totales_data.extend([
            ["", Paragraph("<b>Impuesto (IGV 18%):</b>", negrita), f"S/ {impuesto_val:.2f}"],
            ["", Paragraph("<b>TOTAL A PAGAR:</b>", negrita), f"S/ {total_val:.2f}"]
        ])

        tabla_totales = Table(totales_data, colWidths=[305, 135, 100])
        tabla_totales.setStyle(TableStyle([
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('BOX', (1,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('BACKGROUND', (1,-1), (-1,-1), colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (1,0), (-1,-1), 3),
            ('BOTTOMPADDING', (1,0), (-1,-1), 3),
        ]))
        elementos.append(tabla_totales)
        elementos.append(Spacer(1, 15))

        # 5. Pie de página institucional y advertencia académica
        pie_estilo = ParagraphStyle(
            'Pie',
            parent=estilos['Normal'],
            fontSize=7.5,
            textColor=colors.HexColor("#64748b"),
            alignment=1
        )
        elementos.append(Paragraph("¡Gracias por su preferencia en TechStore Computadoras!", pie_estilo))
        elementos.append(Paragraph("Garantía técnica de hardware: 12 meses conservando este comprobante físico o digital.", pie_estilo))
        elementos.append(Paragraph("<i>Comprobante emitido con fines demostrativos para proyecto académico de software. No constituye comprobante tributario SUNAT.</i>", pie_estilo))

        doc.build(elementos)
        return True, ruta_salida
