"""
Vista de Reportes y Comprobantes:
- Filtro por rango de fechas (Fecha Inicial y Fecha Final con validación AAAA-MM-DD).
- Detalle de ventas, productos vendidos, cantidades, descuentos y totales.
- Reporte de inventario con código, producto, categoría, stock actual y stock mínimo.
- Exportación a Excel (.xlsx) con openpyxl en la carpeta 'documentos_generados/reportes'.
- Generación y reimpresión de comprobantes PDF con ReportLab en 'documentos_generados/comprobantes'.
- Manejo robusto de errores sin cerrar la aplicación.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from models.venta import VentaModel
from models.producto import ProductoModel
from services.excel_service import ExcelService
from services.pdf_service import PDFService
from ui.theme import Color
from ui.widgets import Formulario

class ReportesView(ttk.Frame):
    def __init__(self, parent, usuario_sesion=None):
        super().__init__(parent)
        self.usuario_sesion = usuario_sesion or {"rol": "administrador"}
        self.venta_seleccionada_id = None
        self._construir_ui()
        self.establecer_fechas_mes_actual()
        self.cargar_ventas()
        self.actualizar_indicadores()

    def _construir_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=3) # Tabla de ventas
        self.rowconfigure(3, weight=2) # Tabla de detalles

        # 1. Tarjetas de Resumen / Métricas rápidas
        frame_metricas = ttk.Frame(self, padding=8)
        frame_metricas.grid(row=0, column=0, sticky="ew")
        for i in range(4):
            frame_metricas.columnconfigure(i, weight=1)

        self.card_ingresos = self._crear_tarjeta(frame_metricas, 0, "Ingresos Filtrados", "S/ 0.00", Color.ACENTO_OSCURO)
        self.card_num_ventas = self._crear_tarjeta(frame_metricas, 1, "Ventas Realizadas", "0", Color.TEAL)
        self.card_descuentos = self._crear_tarjeta(frame_metricas, 2, "Descuentos Otorgados", "S/ 0.00", Color.ADVERTENCIA_OSCURO)
        self.card_stock_alerta = self._crear_tarjeta(frame_metricas, 3, "Alertas Stock Bajo", "0", Color.PELIGRO_OSCURO)

        # 2. Barra de filtros por rango de fechas y búsqueda
        frame_filtros = Formulario(self, "Filtros del Reporte")
        frame_filtros.grid(row=1, column=0, sticky="ew", padx=12, pady=6)
        frame_filtros.columnconfigure(1, weight=0)

        fila_fechas = ttk.Frame(frame_filtros)
        ttk.Label(fila_fechas, text="Desde (AAAA-MM-DD)", style="Campo.TLabel").pack(side="left")
        self.entry_fecha_ini = ttk.Entry(fila_fechas, width=12)
        self.entry_fecha_ini.pack(side="left", padx=(6, 14))
        ttk.Label(fila_fechas, text="Hasta (AAAA-MM-DD)", style="Campo.TLabel").pack(side="left")
        self.entry_fecha_fin = ttk.Entry(fila_fechas, width=12)
        self.entry_fecha_fin.pack(side="left", padx=(6, 14))
        ttk.Button(fila_fechas, text="Filtrar periodo", style="Accent.TButton",
                   command=self.cargar_ventas).pack(side="left", padx=(0, 10))
        ttk.Button(fila_fechas, text="Hoy", command=self.establecer_fechas_hoy).pack(side="left", padx=2)
        ttk.Button(fila_fechas, text="Este mes", command=self.establecer_fechas_mes_actual).pack(side="left", padx=2)
        ttk.Button(fila_fechas, text="Ver todo", command=self.limpiar_fechas).pack(side="left", padx=2)
        frame_filtros.ancho(fila_fechas, pady=(0, 6))

        fila_busqueda = ttk.Frame(frame_filtros)
        ttk.Label(fila_busqueda, text="Buscar", style="Campo.TLabel").pack(side="left")
        self.entry_buscar = ttk.Entry(fila_busqueda, width=30)
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.cargar_ventas())
        frame_filtros.ancho(fila_busqueda, pady=(0, 6))

        fila_exportar = ttk.Frame(frame_filtros)
        ttk.Button(fila_exportar, text="Exportar inventario a Excel",
                   command=self.exportar_inventario_excel).pack(side="left", padx=(0, 6))
        ttk.Button(fila_exportar, text="Exportar ventas a Excel",
                   command=self.exportar_ventas_excel).pack(side="left", padx=(0, 6))
        ttk.Button(fila_exportar, text="Ver / reimprimir boleta PDF",
                   command=self.reimprimir_comprobante).pack(side="left")
        frame_filtros.ancho(fila_exportar, pady=(0, 0))

        # 3. Tabla Superior: Listado de Ventas en el Periodo
        frame_tabla_v = ttk.LabelFrame(self, text=" Ventas Realizadas en el Periodo (Seleccione una fila para ver el detalle de productos) ", padding=8)
        frame_tabla_v.grid(row=2, column=0, sticky="nsew", padx=10, pady=4)
        frame_tabla_v.rowconfigure(0, weight=1)
        frame_tabla_v.columnconfigure(0, weight=1)

        cols_v = ("id", "comprobante", "tipo", "fecha", "cliente", "vendedor", "subtotal", "descuento", "impuesto", "total", "metodo")
        self.tree_ventas = ttk.Treeview(frame_tabla_v, columns=cols_v, show="headings", selectmode="browse")

        self.tree_ventas.heading("id", text="ID")
        self.tree_ventas.heading("comprobante", text="N° Comprobante")
        self.tree_ventas.heading("tipo", text="Tipo")
        self.tree_ventas.heading("fecha", text="Fecha y Hora")
        self.tree_ventas.heading("cliente", text="Cliente")
        self.tree_ventas.heading("vendedor", text="Vendedor")
        self.tree_ventas.heading("subtotal", text="Subtotal")
        self.tree_ventas.heading("descuento", text="Descuento")
        self.tree_ventas.heading("impuesto", text="IGV (18%)")
        self.tree_ventas.heading("total", text="Total Pagado")
        self.tree_ventas.heading("metodo", text="Método Pago")

        self.tree_ventas.column("id", width=35, anchor="center")
        self.tree_ventas.column("comprobante", width=110, anchor="center")
        self.tree_ventas.column("tipo", width=70, anchor="center")
        self.tree_ventas.column("fecha", width=130, anchor="center")
        self.tree_ventas.column("cliente", width=180, anchor="w")
        self.tree_ventas.column("vendedor", width=110, anchor="w")
        self.tree_ventas.column("subtotal", width=85, anchor="e")
        self.tree_ventas.column("descuento", width=80, anchor="e")
        self.tree_ventas.column("impuesto", width=75, anchor="e")
        self.tree_ventas.column("total", width=95, anchor="e")
        self.tree_ventas.column("metodo", width=120, anchor="center")

        scroll_vy = ttk.Scrollbar(frame_tabla_v, orient="vertical", command=self.tree_ventas.yview)
        scroll_vx = ttk.Scrollbar(frame_tabla_v, orient="horizontal", command=self.tree_ventas.xview)
        self.tree_ventas.configure(yscrollcommand=scroll_vy.set, xscrollcommand=scroll_vx.set)

        self.tree_ventas.grid(row=0, column=0, sticky="nsew")
        scroll_vy.grid(row=0, column=1, sticky="ns")
        scroll_vx.grid(row=1, column=0, sticky="ew")

        self.tree_ventas.bind("<<TreeviewSelect>>", self._on_venta_seleccionada)

        # 4. Tabla Inferior: Detalle de Productos Vendidos de la Venta Seleccionada
        frame_tabla_d = ttk.LabelFrame(self, text=" Detalle de Productos Vendidos en la Venta Seleccionada ", padding=8)
        frame_tabla_d.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4, 8))
        frame_tabla_d.rowconfigure(0, weight=1)
        frame_tabla_d.columnconfigure(0, weight=1)

        cols_d = ("num", "codigo", "producto", "marca", "cantidad", "precio", "subtotal")
        self.tree_detalles = ttk.Treeview(frame_tabla_d, columns=cols_d, show="headings", selectmode="browse")

        self.tree_detalles.heading("num", text="#")
        self.tree_detalles.heading("codigo", text="Código SKU")
        self.tree_detalles.heading("producto", text="Producto / Componente")
        self.tree_detalles.heading("marca", text="Marca")
        self.tree_detalles.heading("cantidad", text="Cantidad")
        self.tree_detalles.heading("precio", text="Precio Unitario")
        self.tree_detalles.heading("subtotal", text="Subtotal Ítem")

        self.tree_detalles.column("num", width=35, anchor="center")
        self.tree_detalles.column("codigo", width=100, anchor="center")
        self.tree_detalles.column("producto", width=380, anchor="w")
        self.tree_detalles.column("marca", width=110, anchor="w")
        self.tree_detalles.column("cantidad", width=80, anchor="center")
        self.tree_detalles.column("precio", width=110, anchor="e")
        self.tree_detalles.column("subtotal", width=120, anchor="e")

        scroll_dy = ttk.Scrollbar(frame_tabla_d, orient="vertical", command=self.tree_detalles.yview)
        self.tree_detalles.configure(yscrollcommand=scroll_dy.set)

        self.tree_detalles.grid(row=0, column=0, sticky="nsew")
        scroll_dy.grid(row=0, column=1, sticky="ns")

    def _crear_tarjeta(self, parent, col, titulo, valor_inicial, color_fondo):
        frame = tk.Frame(parent, bg=color_fondo, padx=12, pady=8)
        frame.grid(row=0, column=col, sticky="nsew", padx=4)

        lbl_tit = tk.Label(frame, text=titulo.upper(), font=("Segoe UI", 8, "bold"), fg=Color.BLANCO, bg=color_fondo)
        lbl_tit.pack(anchor="w")

        lbl_val = tk.Label(frame, text=valor_inicial, font=("Segoe UI", 14, "bold"), fg=Color.BLANCO, bg=color_fondo)
        lbl_val.pack(anchor="w", pady=(2, 0))
        return lbl_val

    def establecer_fechas_hoy(self):
        hoy = datetime.now().strftime("%Y-%m-%d")
        self.entry_fecha_ini.delete(0, tk.END)
        self.entry_fecha_ini.insert(0, hoy)
        self.entry_fecha_fin.delete(0, tk.END)
        self.entry_fecha_fin.insert(0, hoy)
        self.cargar_ventas()

    def establecer_fechas_mes_actual(self):
        ahora = datetime.now()
        ini_mes = ahora.strftime("%Y-%m-01")
        hoy = ahora.strftime("%Y-%m-%d")
        self.entry_fecha_ini.delete(0, tk.END)
        self.entry_fecha_ini.insert(0, ini_mes)
        self.entry_fecha_fin.delete(0, tk.END)
        self.entry_fecha_fin.insert(0, hoy)
        self.cargar_ventas()

    def limpiar_fechas(self):
        self.entry_fecha_ini.delete(0, tk.END)
        self.entry_fecha_fin.delete(0, tk.END)
        self.cargar_ventas()

    def validar_fechas(self):
        """Valida que las fechas tengan formato AAAA-MM-DD y que fecha_ini <= fecha_fin."""
        f_ini = self.entry_fecha_ini.get().strip()
        f_fin = self.entry_fecha_fin.get().strip()

        if not f_ini and not f_fin:
            return True, None, None, None

        d_ini = None
        d_fin = None

        if f_ini:
            try:
                d_ini = datetime.strptime(f_ini, "%Y-%m-%d").date()
            except ValueError:
                return False, "La Fecha Inicial es inválida. Ingrese el formato AAAA-MM-DD (ej: 2026-10-01).", None, None

        if f_fin:
            try:
                d_fin = datetime.strptime(f_fin, "%Y-%m-%d").date()
            except ValueError:
                return False, "La Fecha Final es inválida. Ingrese el formato AAAA-MM-DD (ej: 2026-10-31).", None, None

        if d_ini and d_fin and d_ini > d_fin:
            return False, "La Fecha Inicial no puede ser posterior a la Fecha Final.", None, None

        f_ini_str = d_ini.strftime("%Y-%m-%d") if d_ini else None
        f_fin_str = d_fin.strftime("%Y-%m-%d") if d_fin else None
        return True, None, f_ini_str, f_fin_str

    def cargar_ventas(self):
        ok, err, f_ini, f_fin = self.validar_fechas()
        if not ok:
            messagebox.showwarning("Fechas Inválidas", err, parent=self)
            return

        for item in self.tree_ventas.get_children():
            self.tree_ventas.delete(item)

        for item in self.tree_detalles.get_children():
            self.tree_detalles.delete(item)

        texto = self.entry_buscar.get().strip()

        try:
            ventas = VentaModel.listar_ventas(fecha_inicio=f_ini, fecha_fin=f_fin, busqueda=texto)
        except Exception as e:
            messagebox.showerror("Error de Base de Datos", f"No se pudo consultar las ventas:\n{str(e)}", parent=self)
            return

        total_ingresos = 0.0
        total_descuentos = 0.0

        for v in ventas:
            tot = float(v.get("total", 0.0))
            sub = float(v.get("subtotal", 0.0))
            desc = float(v.get("descuento", 0.0))
            igv = float(v.get("impuesto", 0.0))

            total_ingresos += tot
            total_descuentos += desc

            vendedor_txt = v.get("vendedor_nombre") or v.get("vendedor_username") or "Admin"

            self.tree_ventas.insert("", "end", values=(
                v["id"],
                v["numero_comprobante"],
                v["tipo_comprobante"],
                v["fecha"],
                v["cliente_nombre"] or "Público General",
                vendedor_txt,
                f"S/ {sub:.2f}",
                f"-S/ {desc:.2f}",
                f"S/ {igv:.2f}",
                f"S/ {tot:.2f}",
                v["metodo_pago"]
            ))

        self.card_ingresos.config(text=f"S/ {total_ingresos:,.2f}")
        self.card_num_ventas.config(text=str(len(ventas)))
        self.card_descuentos.config(text=f"S/ {total_descuentos:,.2f}")

    def actualizar_indicadores(self):
        try:
            bajos = ProductoModel.obtener_productos_bajo_stock()
            self.card_stock_alerta.config(text=str(len(bajos)))
        except Exception:
            pass

    def _on_venta_seleccionada(self, event=None):
        """Carga en la tabla inferior los productos vendidos de la venta seleccionada."""
        sel = self.tree_ventas.selection()
        if not sel:
            return

        item = self.tree_ventas.item(sel[0])
        venta_id = item["values"][0]
        self.venta_seleccionada_id = venta_id

        for row in self.tree_detalles.get_children():
            self.tree_detalles.delete(row)

        try:
            venta_completa = VentaModel.obtener_venta_completa(venta_id)
            if not venta_completa:
                return

            for i, d in enumerate(venta_completa.get("detalles", []), start=1):
                self.tree_detalles.insert("", "end", values=(
                    i,
                    d.get("codigo", "-"),
                    d.get("nombre", "-"),
                    d.get("marca") or "-",
                    d.get("cantidad", 1),
                    f"S/ {float(d.get('precio_unitario', 0.0)):.2f}",
                    f"S/ {float(d.get('subtotal', 0.0)):.2f}"
                ))
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el detalle de la venta:\n{str(e)}", parent=self)

    def exportar_inventario_excel(self):
        """Exporta el inventario con código, producto, categoría, stock actual y stock mínimo."""
        try:
            productos = ProductoModel.listar_productos()
            if not productos:
                messagebox.showwarning("Aviso", "No hay productos en el inventario para exportar.", parent=self)
                return

            carpeta = ExcelService.obtener_carpeta_reportes()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_defecto = os.path.join(carpeta, f"Reporte_Inventario_{timestamp}.xlsx")

            ruta = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                initialdir=carpeta,
                initialfile=os.path.basename(ruta_defecto),
                title="Guardar Reporte de Inventario en Excel"
            )
            if not ruta:
                return

            ExcelService.exportar_inventario(productos, ruta)

            abrir = messagebox.askyesno(
                "Exportación Exitosa",
                f"✔ Reporte de inventario exportado exitosamente.\n\n"
                f"• Ubicación del archivo generado:\n{ruta}\n\n"
                f"¿Desea abrir el archivo Excel ahora?",
                parent=self
            )
            if abrir:
                try:
                    os.startfile(ruta)
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Error al Exportar Inventario", f"Ocurrió un error al generar el archivo Excel:\n{str(e)}", parent=self)

    def exportar_ventas_excel(self):
        """Exporta el reporte detallado de ventas por rango de fechas (productos, cantidades, descuentos y totales)."""
        ok, err, f_ini, f_fin = self.validar_fechas()
        if not ok:
            messagebox.showwarning("Fechas Inválidas", err, parent=self)
            return

        try:
            texto = self.entry_buscar.get().strip()
            detalles_ventas = VentaModel.obtener_ventas_detalladas_rango(
                fecha_inicio=f_ini,
                fecha_fin=f_fin,
                busqueda=texto
            )

            if not detalles_ventas:
                messagebox.showwarning("Aviso", "No se encontraron ventas en el rango de fechas seleccionado.", parent=self)
                return

            carpeta = ExcelService.obtener_carpeta_reportes()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ruta_defecto = os.path.join(carpeta, f"Reporte_Ventas_{timestamp}.xlsx")

            ruta = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                initialdir=carpeta,
                initialfile=os.path.basename(ruta_defecto),
                title="Guardar Reporte Detallado de Ventas en Excel"
            )
            if not ruta:
                return

            ExcelService.exportar_ventas_detallado(
                ventas_detalladas=detalles_ventas,
                ruta_salida=ruta,
                fecha_inicio=f_ini,
                fecha_fin=f_fin
            )

            abrir = messagebox.askyesno(
                "Exportación Exitosa",
                f"✔ Reporte de ventas exportado exitosamente.\n\n"
                f"• Rango: {f_ini or 'Inicio'} al {f_fin or 'Fin'}\n"
                f"• Total registros detallados: {len(detalles_ventas)}\n"
                f"• Ubicación del archivo generado:\n{ruta}\n\n"
                f"¿Desea abrir el archivo Excel ahora?",
                parent=self
            )
            if abrir:
                try:
                    os.startfile(ruta)
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Error al Exportar Ventas", f"Ocurrió un error al generar el archivo Excel:\n{str(e)}", parent=self)

    def reimprimir_comprobante(self):
        """Genera y abre el comprobante PDF de la venta seleccionada."""
        sel = self.tree_ventas.selection()
        if not sel:
            messagebox.showwarning("Atención", "Seleccione primero una venta de la tabla para generar su comprobante PDF.", parent=self)
            return

        item = self.tree_ventas.item(sel[0])
        venta_id = item["values"][0]

        try:
            venta_completa = VentaModel.obtener_venta_completa(venta_id)
            if not venta_completa:
                messagebox.showerror("Error", "No se encontraron los datos de la venta seleccionada.", parent=self)
                return

            carpeta = PDFService.obtener_carpeta_comprobantes()
            num_seguro = str(venta_completa["numero_comprobante"]).replace("/", "_").replace("-", "_")
            pdf_path = os.path.join(carpeta, f"Comprobante_{num_seguro}.pdf")

            PDFService.generar_comprobante_pdf(venta_completa, pdf_path)

            abrir = messagebox.askyesno(
                "Comprobante Generado",
                f"✔ Comprobante PDF generado correctamente.\n\n"
                f"• Documento: {venta_completa['tipo_comprobante']} {venta_completa['numero_comprobante']}\n"
                f"• Ubicación del archivo:\n{pdf_path}\n\n"
                f"¿Desea abrir el comprobante PDF ahora?",
                parent=self
            )
            if abrir:
                try:
                    os.startfile(pdf_path)
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Error al Generar PDF", f"Ocurrió un error al generar el comprobante PDF:\n{str(e)}", parent=self)
