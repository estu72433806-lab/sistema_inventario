"""
Servicio para la exportación de reportes a Microsoft Excel (.xlsx) con openpyxl.
Genera reportes de inventario y reportes detallados de ventas por rango de fechas,
guardando los archivos en la carpeta 'documentos_generados/reportes'.
"""
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ExcelService:
    @staticmethod
    def obtener_carpeta_reportes():
        """Retorna y asegura la existencia de la carpeta 'documentos_generados/reportes'."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        carpeta = os.path.join(base_dir, "documentos_generados", "reportes")
        os.makedirs(carpeta, exist_ok=True)
        return carpeta

    @staticmethod
    def _aplicar_estilo_cabecera(ws, fila, columnas):
        """Aplica estilos visuales elegantes a la cabecera de la tabla."""
        fuente_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        borde_header = Border(
            left=Side(style='thin', color='CBD5E1'),
            right=Side(style='thin', color='CBD5E1'),
            top=Side(style='thin', color='CBD5E1'),
            bottom=Side(style='thin', color='CBD5E1')
        )
        
        for col_idx, texto in enumerate(columnas, start=1):
            celda = ws.cell(row=fila, column=col_idx, value=texto)
            celda.font = fuente_header
            celda.fill = fill_header
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            celda.border = borde_header
        ws.row_dimensions[fila].height = 24

    @staticmethod
    def _ajustar_ancho_columnas(ws):
        """Calcula y ajusta automáticamente el ancho de cada columna según el texto."""
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or '')
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 13)

    @classmethod
    def exportar_inventario(cls, productos, ruta_salida=None):
        """
        Exporta el reporte de inventario mostrando: Código, Producto, Categoría, Stock Actual y Stock Mínimo.
        Resalta en rojo suave aquellos componentes con stock igual o menor al mínimo.
        """
        if not ruta_salida:
            carpeta = cls.obtener_carpeta_reportes()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_salida = os.path.join(carpeta, f"Reporte_Inventario_{timestamp}.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte de Inventario"

        # 1. Título institucional
        ws.merge_cells("A1:F1")
        celda_titulo = ws["A1"]
        celda_titulo.value = "TECHSTORE - REPORTE DE INVENTARIO Y CONTROL DE STOCK"
        celda_titulo.font = Font(name="Calibri", size=13, bold=True, color="0F172A")
        celda_titulo.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        ws.merge_cells("A2:F2")
        ws["A2"].value = f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Total de ítems evaluados: {len(productos)}"
        ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="64748B")
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

        # 2. Encabezados de tabla
        columnas = [
            "Código SKU",
            "Producto / Componente",
            "Categoría",
            "Stock Actual",
            "Stock Mínimo",
            "Estado / Alerta"
        ]
        cls._aplicar_estilo_cabecera(ws, 4, columnas)

        # 3. Estilos de datos
        fill_alerta = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        fuente_alerta = Font(name="Calibri", size=10, bold=True, color="991B1B")
        fuente_normal = Font(name="Calibri", size=10)
        borde_celda = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        fila_actual = 5
        total_unidades = 0
        total_bajo_stock = 0

        for p in productos:
            stock = int(p.get("stock", 0))
            stock_min = int(p.get("stock_minimo", 0))
            es_bajo = (stock <= stock_min)

            if es_bajo:
                total_bajo_stock += 1
                estado_txt = "⚠ STOCK BAJO"
            else:
                estado_txt = "✔ Óptimo"

            total_unidades += stock

            fila_valores = [
                p.get("codigo", "-"),
                p.get("nombre", "-"),
                p.get("categoria_nombre") or "-",
                stock,
                stock_min,
                estado_txt
            ]

            for col_idx, val in enumerate(fila_valores, start=1):
                c = ws.cell(row=fila_actual, column=col_idx, value=val)
                c.font = fuente_normal
                c.border = borde_celda

                if col_idx in (1, 4, 5, 6):
                    c.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="left", vertical="center")

                if es_bajo and col_idx in (4, 6):
                    c.fill = fill_alerta
                    c.font = fuente_alerta

            fila_actual += 1

        # 4. Fila de Resumen al final
        ws.cell(row=fila_actual, column=3, value="TOTAL UNIDADES:").font = Font(name="Calibri", size=10, bold=True)
        ws.cell(row=fila_actual, column=3).alignment = Alignment(horizontal="right")

        celda_tot_stock = ws.cell(row=fila_actual, column=4, value=total_unidades)
        celda_tot_stock.font = Font(name="Calibri", size=10, bold=True)
        celda_tot_stock.alignment = Alignment(horizontal="center")

        ws.cell(row=fila_actual, column=6, value=f"{total_bajo_stock} con stock crítico").font = Font(name="Calibri", size=9, bold=True, color="991B1B")
        ws.cell(row=fila_actual, column=6).alignment = Alignment(horizontal="center")

        cls._ajustar_ancho_columnas(ws)
        wb.save(ruta_salida)
        return True, ruta_salida

    @classmethod
    def exportar_ventas_detallado(cls, ventas_detalladas, ruta_salida=None, fecha_inicio=None, fecha_fin=None):
        """
        Exporta el reporte de ventas con detalle completo:
        - Rango de fechas evaluado
        - Detalle de ventas, productos vendidos, cantidades, descuentos y totales
        """
        if not ruta_salida:
            carpeta = cls.obtener_carpeta_reportes()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_salida = os.path.join(carpeta, f"Reporte_Ventas_Detallado_{timestamp}.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Detallado de Ventas"

        # 1. Título del Reporte
        ws.merge_cells("A1:K1")
        celda_tit = ws["A1"]
        celda_tit.value = "TECHSTORE - REPORTE DETALLADO DE VENTAS Y PRODUCTOS"
        celda_tit.font = Font(name="Calibri", size=13, bold=True, color="0F172A")
        celda_tit.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 28

        # 2. Rango de Fechas
        rango_str = "Historial Completo"
        if fecha_inicio and fecha_fin:
            rango_str = f"Rango de Fechas: Desde {fecha_inicio} Hasta {fecha_fin}"
        elif fecha_inicio:
            rango_str = f"Desde: {fecha_inicio}"

        ws.merge_cells("A2:K2")
        ws["A2"].value = f"{rango_str} | Emitido: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="475569")
        ws["A2"].alignment = Alignment(horizontal="center", vertical="center")

        # 3. Encabezados de Columnas
        columnas = [
            "N° Comprobante",
            "Fecha y Hora",
            "Cliente",
            "Doc. Cliente",
            "Producto Vendido",
            "Cantidad",
            "P. Unitario",
            "Subtotal Ítem",
            "Descuento Venta",
            "Total Venta",
            "Método de Pago"
        ]
        cls._aplicar_estilo_cabecera(ws, 4, columnas)

        # 4. Inserción de Filas de Datos
        fuente_datos = Font(name="Calibri", size=9.5)
        borde_celda = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )

        fila_actual = 5
        total_cantidades = 0
        total_subtotales = 0.0
        ventas_procesadas = set()
        total_descuentos_ventas = 0.0
        total_ventas_general = 0.0

        for reg in ventas_detalladas:
            v_id = reg.get("venta_id")
            cant = int(reg.get("cantidad", 1))
            pu = float(reg.get("precio_unitario", 0.0))
            sub_item = float(reg.get("detalle_subtotal", cant * pu))

            desc_venta = float(reg.get("venta_descuento", 0.0))
            tot_venta = float(reg.get("venta_total", 0.0))

            total_cantidades += cant
            total_subtotales += sub_item

            # Sumar descuento y total solo una vez por venta para no duplicar en filas de múltiples productos
            if v_id not in ventas_procesadas:
                ventas_procesadas.add(v_id)
                total_descuentos_ventas += desc_venta
                total_ventas_general += tot_venta
                desc_display = desc_venta
                tot_display = tot_venta
            else:
                desc_display = 0.0
                tot_display = 0.0

            fila_datos = [
                reg.get("numero_comprobante", "-"),
                reg.get("fecha", "-"),
                reg.get("cliente_nombre") or "Público General",
                reg.get("cliente_doc") or "-",
                f"[{reg.get('producto_codigo', '-')}] {reg.get('producto_nombre', '-')}",
                cant,
                pu,
                sub_item,
                desc_display,
                tot_display,
                reg.get("metodo_pago", "Efectivo")
            ]

            for col_idx, val in enumerate(fila_datos, start=1):
                c = ws.cell(row=fila_actual, column=col_idx, value=val)
                c.font = fuente_datos
                c.border = borde_celda

                if col_idx in (7, 8, 9, 10):
                    c.number_format = 'S/ #,##0.00'
                    c.alignment = Alignment(horizontal="right", vertical="center")
                elif col_idx in (1, 2, 4, 6, 11):
                    c.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    c.alignment = Alignment(horizontal="left", vertical="center")

            fila_actual += 1

        # 5. Fila de Totales Generales
        ws.cell(row=fila_actual, column=5, value="TOTALES:").font = Font(name="Calibri", size=10, bold=True)
        ws.cell(row=fila_actual, column=5).alignment = Alignment(horizontal="right")

        # Total cantidades
        c_tot_cant = ws.cell(row=fila_actual, column=6, value=total_cantidades)
        c_tot_cant.font = Font(name="Calibri", size=10, bold=True)
        c_tot_cant.alignment = Alignment(horizontal="center")

        # Total Subtotales
        c_tot_sub = ws.cell(row=fila_actual, column=8, value=total_subtotales)
        c_tot_sub.font = Font(name="Calibri", size=10, bold=True)
        c_tot_sub.number_format = 'S/ #,##0.00'
        c_tot_sub.alignment = Alignment(horizontal="right")

        # Total Descuentos
        c_tot_desc = ws.cell(row=fila_actual, column=9, value=total_descuentos_ventas)
        c_tot_desc.font = Font(name="Calibri", size=10, bold=True, color="991B1B")
        c_tot_desc.number_format = 'S/ #,##0.00'
        c_tot_desc.alignment = Alignment(horizontal="right")

        # Gran Total de Ventas
        c_tot_gral = ws.cell(row=fila_actual, column=10, value=total_ventas_general)
        c_tot_gral.font = Font(name="Calibri", size=11, bold=True, color="047857")
        c_tot_gral.number_format = 'S/ #,##0.00'
        c_tot_gral.alignment = Alignment(horizontal="right")

        cls._ajustar_ancho_columnas(ws)
        wb.save(ruta_salida)
        return True, ruta_salida

    @classmethod
    def exportar_asistente_reposicion(cls, reporte_data, ruta_salida=None):
        """
        Exporta el informe completo del Asistente de Reposición a Excel (.xlsx).
        Incluye indicadores de urgencia, demanda diaria estimada, cantidades sugeridas
        e información de contacto de proveedores mayoristas para orden de compra.
        """
        if not ruta_salida:
            carpeta = cls.obtener_carpeta_reportes()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_salida = os.path.join(carpeta, f"Recomendacion_Reposicion_{ts}.xlsx")

        wb = Workbook()
        ws = wb.active
        ws.title = "Recomendaciones Reposicion"
        ws.views.sheetView[0].showGridLines = True

        resumen = reporte_data.get("resumen", {})
        sugerencias = reporte_data.get("sugerencias", [])

        # 1. Cabecera Institucional
        ws.merge_cells("A1:G1")
        c_tit = ws["A1"]
        c_tit.value = "TECHSTORE COMPUTADORAS - RECOMENDACIONES DE REPOSICIÓN Y COMPRA"
        c_tit.font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
        c_tit.fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        c_tit.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[1].height = 28

        # 2. Resumen Ejecutivo
        ws["A3"] = "Fecha de Emisión:"
        ws["B3"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws["A4"] = "Ventana de Análisis de Ventas:"
        ws["B4"] = f"Últimos {resumen.get('dias_analisis', 30)} días"
        ws["A5"] = "Horizonte de Cobertura Deseado:"
        ws["B5"] = f"{resumen.get('dias_cobertura_deseada', 30)} días de demanda estimada"

        ws["D3"] = "Total Productos en Catálogo:"
        ws["E3"] = resumen.get("total_catalogo", len(sugerencias))
        ws["D4"] = "Productos que Requieren Compra:"
        ws["E4"] = resumen.get("total_por_reponer", 0)
        ws["D5"] = "Inversión Estimada de Reposición:"
        ws["E5"] = resumen.get("inversion_total_estimada", 0.0)
        ws["E5"].number_format = 'S/ #,##0.00'

        for r in range(3, 6):
            ws[f"A{r}"].font = Font(name="Calibri", size=9, bold=True, color="475569")
            ws[f"B{r}"].font = Font(name="Calibri", size=9)
            ws[f"D{r}"].font = Font(name="Calibri", size=9, bold=True, color="475569")
            ws[f"E{r}"].font = Font(name="Calibri", size=9, bold=True, color="0F172A")

        # 3. Encabezados de la Tabla
        fila_headers = 7
        columnas = [
            "N°", "Urgencia", "Código SKU", "Producto / Modelo", "Categoría",
            "Marca", "Stock Act.", "Stock Mín.", "Ventas (30d)", "Demanda Diaria",
            "Autonomía", "Cant. Sugerida", "P. Compra", "Inversión Est.",
            "Proveedor Sugerido", "Teléfono", "Email Contacto"
        ]
        cls._aplicar_estilo_cabecera(ws, fila_headers, columnas)

        # 4. Inserción de Filas
        borde_celda = Border(
            left=Side(style='thin', color='E2E8F0'),
            right=Side(style='thin', color='E2E8F0'),
            top=Side(style='thin', color='E2E8F0'),
            bottom=Side(style='thin', color='E2E8F0')
        )
        fuente_datos = Font(name="Calibri", size=9)

        # Rellenos por urgencia
        fill_critico = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        fill_urgente = PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid")
        fill_alerta = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        fill_preventivo = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid")

        fila_actual = fila_headers + 1
        total_unidades = 0
        total_inversion = 0.0

        for idx, s in enumerate(sugerencias, start=1):
            urg = s.get("nivel_urgencia", "OPTIMO")
            cant_sug = s.get("cantidad_sugerida", 0)
            costo_est = s.get("costo_estimado", 0.0)

            total_unidades += cant_sug
            total_inversion += costo_est

            autonomia_val = s.get("dias_autonomia")
            autonomia_str = f"{autonomia_val:.1f} d" if autonomia_val is not None else "-"

            fila_datos = [
                idx,
                s.get("urgencia_label", urg),
                s.get("codigo", "-"),
                s.get("nombre", "-"),
                s.get("categoria_nombre", "-"),
                s.get("marca", "-"),
                s.get("stock_actual", 0),
                s.get("stock_minimo", 0),
                s.get("unidades_vendidas_periodo", 0),
                s.get("demanda_diaria", 0.0),
                autonomia_str,
                cant_sug,
                s.get("precio_compra", 0.0),
                costo_est,
                s.get("proveedor_nombre", "-"),
                s.get("proveedor_telefono", "-"),
                s.get("proveedor_email", "-")
            ]

            for c_idx, val in enumerate(fila_datos, start=1):
                celda = ws.cell(row=fila_actual, column=c_idx, value=val)
                celda.font = fuente_datos
                celda.border = borde_celda

                # Formatos
                if c_idx in (13, 14):
                    celda.number_format = 'S/ #,##0.00'
                    celda.alignment = Alignment(horizontal="right", vertical="center")
                elif c_idx in (7, 8, 9, 12):
                    celda.alignment = Alignment(horizontal="center", vertical="center")
                elif c_idx == 10:
                    celda.number_format = '0.00'
                    celda.alignment = Alignment(horizontal="right", vertical="center")
                elif c_idx in (1, 2, 3, 11, 16):
                    celda.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    celda.alignment = Alignment(horizontal="left", vertical="center")

                # Resaltado de fila según urgencia
                if urg == "CRITICO":
                    celda.fill = fill_critico
                elif urg == "URGENTE":
                    celda.fill = fill_urgente
                elif urg == "ALERTA":
                    celda.fill = fill_alerta
                elif urg == "PREVENTIVO":
                    celda.fill = fill_preventivo

            fila_actual += 1

        # 5. Fila de Totales
        ws.cell(row=fila_actual, column=11, value="TOTALES:").font = Font(name="Calibri", size=10, bold=True)
        ws.cell(row=fila_actual, column=11).alignment = Alignment(horizontal="right")

        c_tot_u = ws.cell(row=fila_actual, column=12, value=total_unidades)
        c_tot_u.font = Font(name="Calibri", size=10, bold=True)
        c_tot_u.alignment = Alignment(horizontal="center")

        c_tot_inv = ws.cell(row=fila_actual, column=14, value=total_inversion)
        c_tot_inv.font = Font(name="Calibri", size=10, bold=True, color="047857")
        c_tot_inv.number_format = 'S/ #,##0.00'
        c_tot_inv.alignment = Alignment(horizontal="right")

        cls._ajustar_ancho_columnas(ws)
        wb.save(ruta_salida)
        return True, ruta_salida
